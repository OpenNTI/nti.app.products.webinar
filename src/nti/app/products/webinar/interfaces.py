#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from nti.app.products.integration.interfaces import IIntegration
from nti.app.products.integration.interfaces import IOAuthAuthorizedIntegration

from nti.schema.field import DecodingValidTextLine as ValidTextLine


class IWebinarIntegration(IIntegration):
    """
    A webinar integration
    """


class IWebinarAuthorizedIntegration(IOAuthAuthorizedIntegration,
                                    IWebinarIntegration):
    """
    An :class:`IOAuthAuthorizedIntegration` for webinars.
    """


class IGoToWebinarAuthorizedIntegration(IWebinarAuthorizedIntegration):
    """
    An :class:`IOAuthAuthorizedIntegration` for GOTO webinars.
    """

    organizer_key = ValidTextLine(title=u"GOTOWebinar organizer key",
                                  required=True)

    account_key = ValidTextLine(title=u"GOTOWebinar account key",
                                required=True)


class IWebinarClient(interface.Interface):
    """
    A webinar client to fetch webinar information.
    """

    def get_upcoming_webinars():
        """
        Get all upcoming webinars for our organizer.
        """

    def update_webinar(webinar):
        """
        Update information for the given :class:`IWebinar`.
        """

    def get_webinar_attendees(webinar, session=None):
        """
        Get all attendees for the given :class:`IWebinar`, optionally
        for the given webinar session.
        """

    def get_webinar_sessions(webinar):
        """
        Get all webinar sessions for the given :class:`IWebinar`.
        """

    def get_webinar_registrants(webinar):
        """
        Get all webinar registrants for the given :class:`IWebinar`.
        """

    def get_webinar_registration_fields(webinar):
        """
        Get the registration fields for the given :class:`IWebinar`.
        """
