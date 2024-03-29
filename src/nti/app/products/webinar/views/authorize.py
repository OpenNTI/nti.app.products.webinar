#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import hashlib

from six.moves import urllib_parse

from zope import component

import pyramid.httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.products.webinar import REL_AUTH_WEBINAR

from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar import MessageFactory as _

from nti.app.products.webinar.utils import get_token_data

from nti.common.interfaces import IOAuthKeys

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.intid.common import add_intid

from nti.links.externalization import render_link

from nti.links.links import Link

from nti.site.utils import registerUtility
from nti.site.utils import unregisterUtility

logger = __import__('logging').getLogger(__name__)

AUTH_WEBINAR_OAUTH2 = 'authorize.webinar.oauth2'
WEBINAR_AUTH_URL = 'https://api.getgo.com/oauth/v2/authorize'


def raise_error(data, tb=None, factory=hexc.HTTPBadRequest, request=None):
    request = request or get_current_request()
    failure_redirect = request.session.get('webinar.failure')
    if failure_redirect:
        error_message = data.get('message')
        if error_message:
            parsed = urllib_parse.urlparse(failure_redirect)
            parsed = list(parsed)
            query = parsed[4]
            if query:
                query = query + '&error=' + urllib_parse.quote(error_message)
            else:
                query = 'error=' + urllib_parse.quote(error_message)
            parsed[4] = query
            failure_redirect = urllib_parse.urlunparse(parsed)
        raise hexc.HTTPSeeOther(location=failure_redirect)
    raise_json_error(request, factory, data, tb)


def redirect_webinar_oauth2_uri(request):
    link = Link(request.context, elements=(AUTH_WEBINAR_OAUTH2,))
    link = render_link(link)
    link_href = link.get('href')
    result = urllib_parse.urljoin(request.host_url, link_href)
    return result


def redirect_webinar_oauth2_params(request, state=None):
    auth_keys = component.getUtility(IOAuthKeys, name="webinar")
    state = state or hashlib.sha256(os.urandom(1024)).hexdigest()
    params = {'state': state,
              'response_type': 'code',
              'client_id': auth_keys.APIKey,
              'redirect_uri': redirect_webinar_oauth2_uri(request)}
    return params


@view_config(route_name='objects.generic.traversal',
             context=IWebinarIntegration,
             renderer='rest',
             request_method='GET',
             permission=ACT_CONTENT_EDIT,
             name=REL_AUTH_WEBINAR)
class WebinarAuth(AbstractAuthenticatedView):
    """
    The first step in the webinar auth flow.

    See: https://goto-developer.logmeininc.com/how-get-access-token-and-organizer-key

    e.g. https://api.getgo.com/oauth/v2/authorize?client_id={consumerKey}&response_type=code&state=MyTest&redirect_uri=http%3A%2F%2Fcode.example.com
    """

    def __call__(self):
        request = self.request
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        params = redirect_webinar_oauth2_params(request, state)
        auth_url = WEBINAR_AUTH_URL

        for key in ('success', 'failure'):
            value = request.params.get(key)
            if value:
                request.session['webinar.' + key] = value

        # save state for validation
        request.session['webinar.state'] = state

        # redirect
        target = auth_url[:-1] if auth_url.endswith('/') else auth_url
        target = '%s?%s' % (target, urllib_parse.urlencode(params))
        response = hexc.HTTPSeeOther(location=target)
        return response


@view_config(route_name='objects.generic.traversal',
             context=IWebinarIntegration,
             renderer='rest',
             request_method='GET',
             permission=ACT_CONTENT_EDIT,
             name=AUTH_WEBINAR_OAUTH2)
class WebinarAuth2(AbstractAuthenticatedView):
    """
    The second step in the webinar auth process.

    See: https://goto-developer.logmeininc.com/how-get-access-token-and-organizer-key

    -> http://code.example.com/return/from/oauth/?scope=&code={responseKey}&state=MyTest

    The access_token will expire in 3600 seconds (60 minutes). The refresh_token will
    expire in 30 days.

    Example token response:

    {
     "access_token":"RlUe11faKeyCWxZToK3nk0uTKAL",
     "expires_in":3600,
     "token_type":"Bearer"
     "refresh_token":"d1cp20yB3hrFAKeTokenTr49EZ34kTvNK",
     "organizer_key":"8439885694023999999",
     "account_key":"9999982253621659654",
     "account_type":"",
     "firstName":"Mahar",
     "lastName":"Singh",
     "email":"mahar.singh@singhSong.com",
     "version":"3"
    }
    """

    def _create_auth_integration(self, access_data):
        auth_integration = IGoToWebinarAuthorizedIntegration(access_data)
        auth_integration.creator = self.remoteUser.username
        # Lineage through registry
        auth_integration.__parent__ = component.getSiteManager()
        unregisterUtility(component.getSiteManager(), provided=IGoToWebinarAuthorizedIntegration)
        registerUtility(component.getSiteManager(),
                        component=auth_integration,
                        provided=IGoToWebinarAuthorizedIntegration)
        add_intid(auth_integration)
        auth_integration.store_tokens(access_data['access_token'],
                                      access_data['refresh_token'])
        return auth_integration

    def __call__(self):
        request = self.request
        params = request.params

        # check for errors
        if 'error' in params or 'errorCode' in params:
            error = params.get('error') or params.get('errorCode')
            logger.warn('Error code on webinar auth (%s)', error)
            raise_error({'message': _(u"Error code on webinar auth."),
                         'code': 'WebinarAuthErrorCode'})

        # Confirm code
        if 'code' not in params:
            logger.warn('No code on webinar auth (%s)', params)
            raise_error({'message': _(u"No code on webinar auth."),
                         'code': 'WebinarAuthMissingCode'})
        code = params.get('code')

        # Confirm anti-forgery state token
        if 'state' not in params:
            logger.warn('No state on webinar auth (%s)', params)
            raise_error({'message': _(u"No state on webinar auth."),
                         'code': 'WebinarAuthMissingStateParam'})
        params_state = params.get('state')
        session_state = request.session.get('webinar.state')
        if params_state != session_state:
            logger.warn('Invalid state on webinar auth (%s) (%s)',
                        params_state, session_state)
            raise_error({'message': _(u"Invalid state on webinar auth."),
                         'code': 'WebinarAuthInvalidStateParam'})

        # Exchange code for access and refresh token
        try:
            data = {'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_webinar_oauth2_uri(request)}
            access_data = get_token_data(data)
            auth_integration = self._create_auth_integration(access_data)
            request.environ['nti.request_had_transaction_side_effects'] = 'True'
        except Exception:
            logger.exception('Failed to authorize with webinar')
            raise_error({'message': _(u"Error during webinar authorization."),
                        'code': 'WebinarAuthError'})

        target = request.session.get('webinar.success')
        if target:
            response = hexc.HTTPSeeOther(location=target)
        else:
            response = auth_integration
        return response
