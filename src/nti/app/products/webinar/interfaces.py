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

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.constraints import contains

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from nti.app.products.integration.interfaces import IIntegration
from nti.app.products.integration.interfaces import IOAuthAuthorizedIntegration

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.coremetadata.interfaces import IUser
from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import HTTPURL
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

    def get_webinar(webinar_key, raw=False):
        """
        Get the :class:`IWebinar` for the given key or None; optionally
        returning the raw json.
        """

    def get_all_webinars(raw=False):
        """
        Get all webinars for our organizer; optionally
        returning the raw json.
        """

    def get_upcoming_webinars(raw=False):
        """
        Get all upcoming webinars for our organizer; optionally
        returning the raw json.
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

    def register_user(user, webinar_key, registration_data):
        """
        Register a user given the registration_data.
        """

    def unregister_user(webinar_key, registrant_key):
        """
        Unregister the given registrant key.
        """

    def get_webinar_progress(webinar_key):
        """
        Get all :class:`IUserWebinarProgress` for all sessions of this webinar.
        """


class IWebinarSession(interface.Interface):

    startTime = ValidDatetime(title=u"Webinar session start date",
                              required=True)

    endTime = ValidDatetime(title=u"Webinar session end date",
                            required=True)


class IWebinar(IShouldHaveTraversablePath, IAttributeAnnotatable):

    description = ValidText(title=u"Webinar description",
                            required=True)

    subject = ValidTextLine(title=u"Webinar subject",
                            required=True)

    organizerKey = ValidTextLine(title=u"Webinar organizer key",
                                 required=True)

    webinarKey = ValidTextLine(title=u"Webinar key",
                               required=True)

    numberOfRegistrants = Number(title=u"Webinar registrant count",
                                 required=False)

    timeZone = ValidTextLine(title=u"Webinar timeZone",
                             required=True)

    registrationUrl = HTTPURL(title=u"Webinar registrationUrl",
                              required=False)

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


class IWebinarField(interface.Interface):
    """
    A webinar registration field.
    """

    field = ValidTextLine(title=u"The field name",
                          required=True)

    maxSize = Int(title=u"The max size of the field",
                  required=True)

    required = Bool(title=u"required", required=True)

    answers = ListOrTuple(title=u"Webinar field answers",
                          required=False,
                          min_length=0,
                          value_type=ValidTextLine(title=u"The answer"))


class IWebinarQuestionAnswer(interface.Interface):
    """
    A webinar registration question answer, for multiple choice.
    """

    answerKey = Int(title=u"The answer key",
                    required=True)

    answer = ValidTextLine(title=u"The answer",
                           required=True)


class IWebinarQuestion(interface.Interface):
    """
    A webinar registration question.
    """

    questionKey = Int(title=u"The question key",
                      required=True)

    maxSize = Int(title=u"The max size of the field",
                  required=True)

    required = Bool(title=u"required", required=True)

    type = ValidTextLine(title=u"The question type",
                         required=True)

    question = ValidTextLine(title=u"The question",
                             required=True)

    answers = ListOrTuple(Object(IWebinarQuestionAnswer),
                          title=u"Webinar question answers",
                          required=False,
                          min_length=0)


class IWebinarRegistrationFields(interface.Interface):
    """
    The webinar registration fields.
    """

    fields = ListOrTuple(Object(IWebinarField),
                        title=u"Webinar fields",
                        required=False,
                        min_length=0)

    questions = ListOrTuple(Object(IWebinarQuestion),
                            title=u"Webinar questions",
                            required=False,
                            min_length=0)


class IJoinWebinarEvent(interface.Interface):
    """
    An event that is sent when an LTI asset is launched
    """

    user = Object(IUser,
                  title=u'The user who joined the webinar',
                  required=True)

    webinar = Object(IWebinar,
                   title=u'The webinar that was join.',
                   required=True)

    timestamp = ValidDatetime(title=u'The time at which the webinar was joined',
                              required=True)


@interface.implementer(IJoinWebinarEvent)
class JoinWebinarEvent(object):

    def __init__(self, user, webinar, timestamp):
        self.user = user
        self.webinar = webinar
        self.timestamp = timestamp


class IWebinarRegistrationMetadata(IContained, ICreated, ILastModified):
    """
    A metadata user webinar registration object.
    """

    registrant_key = ValidTextLine(title=u"The registrant key",
                                   required=True)

    organizer_key = ValidTextLine(title=u"Webinar organizer key",
                                  required=True)

    webinar_key = ValidTextLine(title=u"Webinar key",
                                required=True)

    join_url = HTTPURL(title=u"Webinar join url",
                       required=True)


class IWebinarRegistrationMetadataContainer(IContainer):
    """
    A storage container for :class:`IWebinarRegistration` objects.
    """
    contains(IWebinarRegistrationMetadata)


class WebinarClientError(Exception):

    def __init__(self, msg, json=None):
        Exception.__init__(self, msg)
        self.json = json


class WebinarRegistrationError(WebinarClientError):

    msg = 'Error during webinar registration.'

    def __init__(self, json=None):
        super(WebinarRegistrationError, self).__init__(self.msg, json)


class IUserWebinarAttendance(interface.Interface):

    joinTime = ValidDatetime(title=u'The time at which the webinar was joined',
                             required=True)

    leaveTime = ValidDatetime(title=u'The time at which the webinar was left',
                              required=True)


class IUserWebinarProgress(IContained, ILastModified):
    """
    Stores webinar progress for a given user and webinar.
    """

    registrantKey = ValidTextLine(title=u"Webinar registrant key",
                                 required=True)

    sessionKey = ValidTextLine(title=u"Webinar session key",
                               required=True)

    email = ValidTextLine(title=u'Webinar registrant email',
                          required=False)

    attendance = ListOrTuple(Object(IUserWebinarAttendance),
                             title=u"Webinar attendance",
                             required=False,
                             min_length=0)

    attendanceTimeInSeconds = Int(title=u"The webinar time in seconds",
                                  required=True)


class IUserWebinarProgressContainer(IContainer):
    """
    A user progress storage container for a :class:`IWebinar` objects, stored by session.
    """
    contains(IUserWebinarProgress)


class IWebinarProgressContainer(IContainer):
    """
    A progress storage container for :class:`IWebinar` objects.
    """
    contains(IUserWebinarProgressContainer)

    last_updated = ValidDatetime(title=u'The last time webinar progress was updated',
                                 required=True)


import zope.deferredimport
zope.deferredimport.initialize()

zope.deferredimport.deprecatedFrom(
    "Moved to nti.app.products.courseware.webinars.interfaces",
    "nti.app.products.courseware.webinars.interfaces",
    "IWebinarAsset")
