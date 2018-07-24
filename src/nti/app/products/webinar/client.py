#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import requests

from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarCollection
from nti.app.products.webinar.interfaces import WebinarRegistrationError
from nti.app.products.webinar.interfaces import IWebinarRegistrationFields
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadata
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar import MessageFactory as _

from nti.app.products.webinar.utils import raise_error

logger = __import__('logging').getLogger(__name__)


@component.adapter(IGoToWebinarAuthorizedIntegration, IRequest)
@interface.implementer(IWebinarClient)
class GoToWebinarClient(object):
    """
    The client to interact with making GOTO webinar API calls. This should
    live within a single request lifespan.
    """
    GOTO_BASE_URL = 'https://api.getgo.com/G2W/rest'

    WEBINAR_URL = '/organizers/%s/webinars/%s'
    UPCOMING_WEBINARS = '/organizers/%s/upcomingWebinars'

    WEBINAR_SESSIONS = '/organizers/%s/webinars/%s/sessions'
    WEBINAR_ATTENDEES = '/organizers/%s/webinars/%s/attendees'
    SESSION_ATTENDEES = '/organizers/%s/webinars/%s/sessions/%s/attendees'

    REGISTRANTS = '/organizers/%s/webinars/%s/registrants'
    REGISTER_FIELDS = '/organizers/%s/webinars/%s/registrants/fields'

    def __init__(self, authorized_integration, request):
        self.authorized_integration = authorized_integration
        self.request = request
        self._access_token = self.request.session.get('webinar.access_token')

    def _get_access_token(self):
        self._access_token = self.authorized_integration.access_token
        self.request.session['webinar.access_token'] = self._access_token

    def _update_access_token(self):
        result = self.authorized_integration.update_tokens(self._access_token)
        self._access_token = result
        self.request.session['webinar.access_token'] = result

    def _make_call(self, url, post_data=None, acceptable_return_codes=None):
        if not acceptable_return_codes:
            acceptable_return_codes = (200,)
        url = '%s%s' % (self.GOTO_BASE_URL, url)
        if self._access_token is None:
            self._get_access_token()

        def _do_make_call():
            access_header = 'Bearer %s' % self._access_token
            if post_data:
                return requests.post(url,
                                     json=post_data,
                                     headers={'Authorization': access_header,
                                              'Accept': 'application/json'})
            else:
                return requests.get(url,
                                    headers={'Authorization': access_header})
        response = _do_make_call()
        if response.status_code in (401, 403):
            # Ok, expired token, refresh and try again.
            self._update_access_token()
            response = _do_make_call()

        if response.status_code not in acceptable_return_codes:
            logger.warn('Error while making webinar API call (%s) (%s)',
                        response.status_code,
                        response.text)
            raise_error({'message': _(u"Error during webinar call."),
                         'code': 'WebinarClientAPIError'})
        return response

    def get_upcoming_webinars(self):
        url = self.UPCOMING_WEBINARS % self.authorized_integration.organizer_key
        result = self._make_call(url)
        result = IWebinarCollection(result.json())
        return result.webinars

    def get_webinar(self, webinar_key):
        url = self.WEBINAR_URL % (self.authorized_integration.organizer_key, webinar_key)
        get_response = self._make_call(url, acceptable_return_codes=(200, 404))
        result = None
        if get_response.status_code != 404:
            result = IWebinar(get_response.json())
        return result

    def get_registration_fields(self, webinar_key):
        url = self.REGISTER_FIELDS % (self.authorized_integration.organizer_key, webinar_key)
        get_response = self._make_call(url, acceptable_return_codes=(200, 404))
        result = None
        if get_response.status_code != 404:
            result = IWebinarRegistrationFields(get_response.json())
        return result

    def register_user(self, webinar_key, registration_data):
        url = self.REGISTRANTS % (self.authorized_integration.organizer_key,
                                  webinar_key)
        # 409 if user is already registered
        response = self._make_call(url,
                                   post_data=registration_data,
                                   acceptable_return_codes=(201, 400, 409))
        if response.status_code == 400:
            raise WebinarRegistrationError(response.json())

        if response.status_code == 409:
            logger.info('User already registered for webinar')

        # We want to return a metadata object on 409 so we can store it if
        # we have not already.
        data = response.json()
        creator = getattr(self.request.remoteUser, 'username', '')
        data = {'join_url': data.get('joinUrl'),
                'registrant_key': data.get('registrantKey'),
                'webinar_key': webinar_key,
                'organizer_key': self.authorized_integration.organizer_key,
                'creator': creator}
        return IWebinarRegistrationMetadata(data)
