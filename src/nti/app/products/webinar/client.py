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

from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarCollection
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar.utils import raise_error
from nti.app.products.webinar.utils import get_access_token

logger = __import__('logging').getLogger(__name__)


@component.adapter(IGoToWebinarAuthorizedIntegration, IRequest)
@interface.implementer(IWebinarClient)
class GoToWebinarClient(object):
    """
    The client to interact with making GOTO webinar API calls. This should
    live within a single request lifespan.
    """

    GET_WEBINAR = '/organizers/%s/webinars/%s'
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

    def _update_access_token(self):
        self._access_token = get_access_token(self.authorized_integration)
        self.request.session['webinar.access_token'] = self._access_token
        # If fetching access token, we need to store our new refresh token
        self.request.environ['nti.request_had_transaction_side_effects'] = True

    def _make_call(self, url, post_data=None):
        if self._access_token is None:
            self._update_access_token()

        def _do_make_call():
            access_header = 'Bearer %s' % self._access_token
            if post_data:
                return requests.post(url, post_data,
                                     headers={'Authorization': access_header})
            else:
                return requests.get(url,
                                    headers={'Authorization': access_header})
        response = _do_make_call()
        if response.status_code == 401:
            # FIXME: verify this status code on expired token
            # Ok, expired token, refresh and try again.
            self._update_access_token()
            response = _do_make_call()

        if response.status_code != 200:
            logger.warn('Error while making webinar API call (%s) (%s)',
                        response.status_code,
                        response.text)
            raise_error({'message': _(u"Error during webinar call."),
                         'code': 'WebinarClientAPIError'})
        return response.json()

    def get_upcoming_webinars(self):
        url = self.UPCOMING_WEBINARS % self.authorized_integration.organizer_key
        result = self._make_call(url)
        result = IWebinarCollection(result)
        return result

