#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import urllib_parse

import os
import hashlib
import requests

from zope import component

import pyramid.httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.products.webinar import REL_AUTH_WEBINAR

from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration

from nti.app.products.webinar.integration import GoToWebinarAuthorizedIntegration

from nti.appserver import MessageFactory as _

from nti.common.interfaces import IOAuthKeys

from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.site.utils import registerUtility

logger = __import__('logging').getLogger(__name__)

AUTH_WEBINAR_OAUTH2 = 'authorize.webinar.oauth2'
WEBINAR_AUTH_URL = 'https://api.getgo.com/oauth/v2/authorize'
WEBINAR_AUTH_TOKEN_URL = 'https://api.getgo.com/oauth/v2/token'


def raise_error(data, tb=None, factory=hexc.HTTPBadRequest, request=None):
    request = request or get_current_request()
    raise_json_error(request, factory, data, tb)


def redirect_webinar_oauth2_uri(request):
    root = request.route_path('objects.generic.traversal', traverse=())
    root = root[:-1] if root.endswith('/') else root
    target = urllib_parse.urljoin(request.application_url, root)
    target = target + '/' if not target.endswith('/') else target
    target = urllib_parse.urljoin(target, AUTH_WEBINAR_OAUTH2)
    return target


def redirect_webinar_oauth2_params(request, state=None, auth_keys=None):
    if auth_keys is None:
        auth_keys = component.getUtility(IOAuthKeys, name="webinar")
    state = state or hashlib.sha256(os.urandom(1024)).hexdigest()
    params = {'state': state,
              'response_type': 'code',
              'client_id': auth_keys.APIKey,
              'redirect_uri': redirect_webinar_oauth2_uri(request)}
    return params


@view_config(route_name='objects.generic.traversal',
             context=IDataserverFolder,
             renderer='rest',
             request_method='GET',
             name=REL_AUTH_WEBINAR)
class WebinarAuth(AbstractAuthenticatedView):
    """
    The first step in the webinar auth flow.

    See: https://goto-developer.logmeininc.com/how-get-access-token-and-organizer-key

    e.g. https://api.getgo.com/oauth/v2/authorize?client_id={consumerKey}&response_type=code&state=MyTest&redirect_uri=http%3A%2F%2Fcode.example.com
    """

    def _check_access(self):
        return is_admin_or_site_admin(self.remoteUser)

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
             context=IDataserverFolder,
             renderer='rest',
             request_method='GET',
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
        access_token = access_data.get('access_token')
        access_header = 'Bearer %s' % access_token
        self.request.response.headers['Authorization'] = access_header
        refresh_token = access_data.get('refresh_token')
        auth_integration = GoToWebinarAuthorizedIntegration(title='Authorized GOTOWebinar Integration',
                                                            refresh_token=refresh_token)
        registerUtility(component.getSiteManager(),
                        component=auth_integration,
                        provided=IWebinarAuthorizedIntegration)

    def __call__(self):
        from IPython.terminal.debugger import set_trace;set_trace()
        request = self.request
        params = request.params
        auth_keys = component.getUtility(IOAuthKeys, name="webinar")

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
            auth_header = '%s:%s' % (auth_keys.APIKey, auth_keys.secretKey)
            auth_header = 'Basic %s' % auth_header.encode('base64')
            response = requests.post(WEBINAR_AUTH_TOKEN_URL,
                                     data,
                                     headers={'Authorization': auth_header})
            if response.status_code != 200:
                logger.warn('Error while getting webinar token (%s)',
                            response.text)
                raise_error({'message': _(u"Error during webinar auth."),
                             'code': 'WebinarAuthError'})

            access_data = response.json()
            if 'access_token' not in data:
                logger.warn('Missing webinar access token (%s)',
                            access_data)
                raise_error({'message': _(u"No webinar access token"),
                             'code': 'WebinarAuthMissingAccessToken'})
            if 'refresh_token' not in data:
                logger.warn('Missing webinar refresh token (%s)',
                            access_data)
                raise_error({'message': _(u"No webinar refresh token"),
                             'code': 'WebinarAuthMissingRefreshToken'})

            self._create_auth_integration(access_data)
            request.environ['nti.request_had_transaction_side_effects'] = 'True'
        except Exception:
            logger.exception('Failed to authorize with webinar')
            raise_error({'message': _(u"Error during webinar authorization."),
                        'code': 'WebinarAuthError'})
        return response
