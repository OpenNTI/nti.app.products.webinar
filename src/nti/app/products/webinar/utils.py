#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import base64
import requests

import pyramid.httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from six.moves import urllib_parse

from zope import component

from nti.app.externalization.error import raise_json_error

from nti.app.products.webinar import MessageFactory as _

from nti.common.interfaces import IOAuthKeys

logger = __import__('logging').getLogger(__name__)


WEBINAR_AUTH_TOKEN_URL = "https://api.getgo.com/oauth/v2/token"


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


def get_token_data(post_data):
    """
    Get the GOTO webinar token data, using the supplied post_data dict
    for the certain type of token fetch.
    """
    auth_keys = component.getUtility(IOAuthKeys, name="webinar")
    auth_header = '%s:%s' % (auth_keys.APIKey, auth_keys.secretKey)
    auth_header = base64.b64encode(auth_header)
    auth_header = 'Basic %s' % auth_header
    response = requests.post(WEBINAR_AUTH_TOKEN_URL,
                             post_data,
                             headers={'Authorization': auth_header})
    if response.status_code != 200:
        error_json = response.json()
        if 'error' in error_json and error_json['error'] == 'invalid_grant':
            # This is likely a lapsed account that will need to be re-authorized.
            logger.warn('Invalid grant while getting webinar token, may need to be re-authorized (%s)',
                        response.text)
            raise_error({'message': _(u"Error during webinar auth, may need to re-authorize."),
                         'code': 'WebinarInvalidAuthError'})
        else:
            logger.warn('Error while getting webinar token (%s)',
                        response.text)
            raise_error({'message': _(u"Error during webinar auth."),
                         'code': 'WebinarAuthError'})

    access_data = response.json()
    if 'access_token' not in access_data:
        logger.warn('Missing webinar access token (%s)',
                    access_data)
        raise_error({'message': _(u"No webinar access token"),
                     'code': 'WebinarAuthMissingAccessToken'})
    if 'refresh_token' not in access_data:
        logger.warn('Missing webinar refresh token (%s)',
                    access_data)
        raise_error({'message': _(u"No webinar refresh token"),
                     'code': 'WebinarAuthMissingRefreshToken'})
    return access_data


def get_auth_tokens(refresh_token):
    """
    Fetch an access_token and refresh_token
    """
    data = {'refresh_token': refresh_token,
            'grant_type': 'refresh_token'}
    access_data = get_token_data(data)
    return access_data.get('access_token'), access_data.get('refresh_token')
