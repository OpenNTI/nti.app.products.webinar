#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves import urllib_parse

import os
import hashlib
from urlparse import urljoin

import simplejson as json

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.event import notify

from zope.i18n import translate

from zope.traversing import api as ztraversing

import pyramid.request
import pyramid.interfaces
import pyramid.httpexceptions as hexc

from pyramid import security as sec

from pyramid.view import view_config

import requests
from requests.exceptions import RequestException

from nti.app.renderers.interfaces import IResponseCacheController
from nti.app.renderers.interfaces import IPrivateUncacheableInResponse

from nti.appserver import MessageFactory as _

from nti.appserver._util import logon_userid_with_request

from nti.appserver.account_recovery_views import REL_RESET_PASSCODE
from nti.appserver.account_creation_views import REL_CREATE_ACCOUNT
from nti.appserver.account_recovery_views import REL_FORGOT_PASSCODE
from nti.appserver.account_recovery_views import REL_FORGOT_USERNAME
from nti.appserver.account_creation_views import REL_PREFLIGHT_CREATE_ACCOUNT

from nti.appserver.interfaces import ILogonPong
from nti.appserver.interfaces import IMissingUser
from nti.appserver.interfaces import IUserLogonEvent
from nti.appserver.interfaces import ILogonLinkProvider
from nti.appserver.interfaces import IImpersonationDecider
from nti.appserver.interfaces import IAuthenticatedUserLinkProvider
from nti.appserver.interfaces import IUnauthenticatedUserLinkProvider
from nti.appserver.interfaces import ILogoutForgettingResponseProvider
from nti.appserver.interfaces import ILogonUsernameFromIdentityURLProvider

from nti.appserver.interfaces import UserLogoutEvent
from nti.appserver.interfaces import AmbiguousUserLookupError
from nti.appserver.interfaces import UserCreatedWithRequestEvent

from nti.appserver.link_providers import flag_link_provider
from nti.appserver.link_providers import unique_link_providers

from nti.appserver.policies.interfaces import ISitePolicyUserEventListener

from nti.appserver.pyramid_authorization import has_permission

from nti.common.string import is_true

from nti.dataserver import authorization as nauth
from nti.dataserver import interfaces as nti_interfaces

from nti.dataserver.interfaces import IGoogleUser

from nti.dataserver.users.interfaces import GoogleUserCreatedEvent
from nti.dataserver.users.interfaces import OpenIDUserCreatedEvent
from nti.dataserver.users.interfaces import IUsernameGeneratorUtility

from nti.externalization.interfaces import IExternalObject

from nti.links.links import Link

from nti.mimetype import mimetype

from nti.common.interfaces import IOAuthKeys

logger = __import__('logging').getLogger(__name__)

REL_LOGIN_WEBINAR = 'logon.webinar'
LOGON_WEBINAR_OAUTH2 = 'logon.webinar.oauth2'
GOTO_AUTH_URL = 'https://api.getgo.com/oauth/v2/authorize'
#https://api.getgo.com/oauth/v2/authorize?client_id={consumerKey}&response_type=code&state=MyTest&redirect_uri=http%3A%2F%2Fcode.example.com
#oath response -> http://code.example.com/return/from/oauth/?scope=&code={responseKey}&state=MyTest


def redirect_webinar_oauth2_uri(request):
    root = request.route_path('objects.generic.traversal', traverse=())
    root = root[:-1] if root.endswith('/') else root
    target = urljoin(request.application_url, root)
    target = target + '/' if not target.endswith('/') else target
    target = urljoin(target, LOGON_WEBINAR_OAUTH2)
    return target


def redirect_webinar_oauth2_params(request, state=None, auth_keys=None):
    if auth_keys is None:
        auth_keys = component.getUtility(IOAuthKeys, name="webinar")
    state = state or hashlib.sha256(os.urandom(1024)).hexdigest()
    params = {'state': state,
              'scope': 'openid email profile',
              'response_type': 'code',
              'client_id': auth_keys.APIKey,
              'redirect_uri': redirect_webinar_oauth2_uri(request)}
    return params


@view_config(route_name=REL_LOGIN_WEBINAR, request_method='GET')
def webinar_oauth1(request, success=None, failure=None, state=None):
    state = state or hashlib.sha256(os.urandom(1024)).hexdigest()
    config = get_openid_configuration()
    params = redirect_webinar_oauth2_params(request, state)
    auth_url = config.get("authorization_endpoint", DEFAULT_AUTH_URL)

    for key, value in (('success', success), ('failure', failure)):
        value = value or request.params.get(key)
        if value:
            request.session['google.' + key] = value

    # save state for validation
    request.session['google.state'] = state

    # redirect
    target = auth_url[:-1] if auth_url.endswith('/') else auth_url
    target = '%s?%s' % (target, urllib_parse.urlencode(params))
    response = hexc.HTTPSeeOther(location=target)
    return response


@view_config(route_name=LOGON_WEBINAR_OAUTH2, request_method='GET')
def webinar_oauth2(request):
    params = request.params
    auth_keys = component.getUtility(IOAuthKeys, name="webinar")

    # check for errors
    if 'error' in params or 'errorCode' in params:
        error = params.get('error') or params.get('errorCode')
        return _create_failure_response(request,
                                        request.session.get('google.failure'),
                                        error=error)

    # Confirm code
    if 'code' not in params:
        return _create_failure_response(request,
                                        request.session.get('google.failure'),
                                        error=_(u'Could not find code parameter.'))
    code = params.get('code')

    # Confirm anti-forgery state token
    if 'state' not in params:
        return _create_failure_response(request,
                                        request.session.get('google.failure'),
                                        error=_(u'Could not find state parameter.'))
    params_state = params.get('state')
    session_state = request.session.get('google.state')
    if params_state != session_state:
        return _create_failure_response(request,
                                        request.session.get('google.failure'),
                                        error=_(u'Incorrect state values.'))

    # Exchange code for access token and ID token
    config = get_openid_configuration()
    token_url = config.get('token_endpoint', DEFAULT_TOKEN_URL)

    try:
        data = {'code': code,
                'client_id': auth_keys.APIKey,
                'grant_type': 'authorization_code',
                'client_secret': auth_keys.SecretKey,
                'redirect_uri': redirect_webinar_oauth2_uri(request)}
        response = requests.post(token_url, data)
        if response.status_code != 200:
            return _create_failure_response(
                request,
                request.session.get('google.failure'),
                error=_('Invalid response while getting access token.'))

        data = response.json()
        if 'access_token' not in data:
            return _create_failure_response(request,
                                            request.session.get('google.failure'),
                                            error=_(u'Could not find access token.'))
        if 'id_token' not in data:
            return _create_failure_response(request,
                                            request.session.get('google.failure'),
                                            error=_(u'Could not find id token.'))

        # id_token = data['id_token'] #TODO:Validate id token
        access_token = data['access_token']
        logger.debug("Getting user profile")
        userinfo_url = config.get('userinfo_endpoint', DEFAULT_USERINFO_URL)
        response = requests.get(userinfo_url, params={
                                "access_token": access_token})
        if response.status_code != 200:
            return _create_failure_response(request,
                                            request.session.get('google.failure'),
                                            error=_(u'Invalid access token.'))
        profile = response.json()

        response = _create_success_response(request,
                                            userid=user.username,
                                            success=request.session.get('google.success'))
    except Exception as e:
        logger.exception('Failed to login with webinar')
        response = _create_failure_response(request,
                                            request.session.get('google.failure'),
                                            error=str(e))
    return response
