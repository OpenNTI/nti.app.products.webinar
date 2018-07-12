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

from nti.contenttypes.presentation.interfaces import IUserCreatedAsset
from nti.contenttypes.presentation.interfaces import IGroupOverViewable
from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset

from nti.schema.field import Bool
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import ValidText
from nti.schema.field import ListOrTuple
from nti.schema.field import ValidDatetime
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

    webinar_realname = ValidTextLine(title=u'GOTO account realname',
                                     required=False)

    webinar_email = ValidTextLine(title=u'GOTO account email',
                                  required=False)

    webinar_email.setTaggedValue('_ext_excluded_out', True)


class IWebinarClient(interface.Interface):
    """
    A webinar client to fetch webinar information.
    """

    def get_webinar(webinar_key):
        """
        Get the :class:`IWebinar` for the given key or None.
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


class IWebinarSession(interface.Interface):

    startTime = ValidDatetime(title=u"Webinar session start date",
                              required=True)

    endTime = ValidDatetime(title=u"Webinar session end date",
                            required=True)


class IWebinar(interface.Interface):

    description = ValidText(title=u"Webinar description",
                            required=True)

    subject = ValidTextLine(title=u"Webinar subject",
                            required=True)

    organizerKey = Number(title=u"Webinar organizer key",
                          required=True)

    webinarKey = Number(title=u"Webinar key",
                        required=True)

    numberOfRegistrants = Number(title=u"Webinar registrant count",
                                 required=False)

    timeZone = ValidTextLine(title=u"Webinar timeZone",
                             required=True)

    registrationUrl = ValidTextLine(title=u"Webinar registrationUrl",
                                    required=True)

    webinarID = ValidTextLine(title=u"Webinar webinarID",
                              required=True)

    inSession = Bool(title=u"Webinar is in session",
                     required=True)

    times = ListOrTuple(Object(IWebinarSession),
                        title=u"Webinar sessions",
                        required=True,
                        min_length=1)


class IWebinarCollection(interface.Interface):

    webinars = ListOrTuple(Object(IWebinar),
                           title=u"Webinar objects",
                           required=True,
                           min_length=0)


class IWebinarAsset(ICoursePresentationAsset,
                    IUserCreatedAsset,
                    IGroupOverViewable):
    """
    A presentation asset for webinars.
    """

    title = ValidTextLine(title=u"The webinar asset title",
                          required=False)

    description = ValidTextLine(title=u"The webinar asset description",
                                required=False)

    webinar = Object(IWebinar, required=True)
