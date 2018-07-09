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

from nti.app.products.integration.interfaces import IIntegrationCollectionProvider

from nti.app.products.integration.integration import AbstractIntegration
from nti.app.products.integration.integration import AbstractOAuthAuthorizedIntegration

from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar.utils import get_access_token

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

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

    def _make_call(self, url):
        if self._access_token is None:
            self._update_access_token()
        access_header = 'Bearer %s' % self._access_token
        response = requests.get(url,
                                headers={'Authorization': access_header})

    def get_upcoming_webinars(self):
        url = self.UPCOMING_WEBINARS % self.authorized_integration.organizer_key
        result = self._make_call(url)
        return result

