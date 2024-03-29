#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarField
from nti.app.products.webinar.interfaces import IWebinarSession
from nti.app.products.webinar.interfaces import IWebinarQuestion
from nti.app.products.webinar.interfaces import IWebinarCollection
from nti.app.products.webinar.interfaces import IUserWebinarProgress
from nti.app.products.webinar.interfaces import IWebinarQuestionAnswer
from nti.app.products.webinar.interfaces import IUserWebinarAttendance
from nti.app.products.webinar.interfaces import IWebinarRegistrationFields
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadata

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.internalization import update_from_external_object

from nti.externalization.representation import WithRepr

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@component.adapter(dict)
@interface.implementer(IWebinarField)
def _webinar_field_factory(ext):
    obj = WebinarField()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinarQuestion)
def _webinar_question_factory(ext):
    obj = WebinarQuestion()
    if 'answers' in ext:
        ext['answers'] = [IWebinarQuestionAnswer(x) for x in ext['answers'] or ()]
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinarQuestionAnswer)
def _webinar_question_answer_factory(ext):
    obj = WebinarQuestionAnswer()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinarRegistrationFields)
def _webinar_registration_fields_factory(ext):
    obj = WebinarRegistrationFields()
    ext['fields'] = [IWebinarField(x) for x in ext['fields'] or ()]
    ext['questions'] = [IWebinarQuestion(x) for x in ext['questions'] or ()]
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinar)
def _webinar_factory(ext):
    obj = Webinar()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinarSession)
def _webinar_session_factory(ext):
    obj = WebinarSession()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(list)
@interface.implementer(IWebinarCollection)
def _webinar_collection_factory(ext):
    obj = WebinarCollection()
    new_ext = dict()
    new_ext['webinars'] = [IWebinar(x) for x in ext or ()]
    update_from_external_object(obj, new_ext)
    return obj


@component.adapter(dict)
@interface.implementer(IWebinarRegistrationMetadata)
def _webinar_registration_metadata_factory(ext):
    obj = WebinarRegistrationMetadata()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IUserWebinarAttendance)
def _user_webinar_attendance_factory(ext):
    obj = UserWebinarAttendance()
    update_from_external_object(obj, ext)
    return obj


@component.adapter(dict)
@interface.implementer(IUserWebinarProgress)
def _user_webinar_progress_factory(ext):
    obj = UserWebinarProgress()
    for key in ('registrantKey', 'sessionKey'):
        if key in ext:
            ext[key] = str(ext[key])
    if 'attendance' in ext:
        ext['attendance'] = [IUserWebinarAttendance(x) for x in ext['attendance']]
    update_from_external_object(obj, ext)
    return obj


@interface.implementer(IWebinarField)
class WebinarField(SchemaConfigured):

    createDirectFieldProperties(IWebinarField)

    mimeType = mime_type = "application/vnd.nextthought.webinarfield"


@interface.implementer(IWebinarQuestionAnswer)
class WebinarQuestionAnswer(SchemaConfigured):

    createDirectFieldProperties(IWebinarQuestionAnswer)

    mimeType = mime_type = "application/vnd.nextthought.webinarquestionanswer"


@interface.implementer(IWebinarQuestion)
class WebinarQuestion(SchemaConfigured):

    createDirectFieldProperties(IWebinarQuestion)

    mimeType = mime_type = "application/vnd.nextthought.webinarquestion"


@interface.implementer(IWebinarRegistrationFields)
class WebinarRegistrationFields(SchemaConfigured):

    createDirectFieldProperties(IWebinarRegistrationFields)

    mimeType = mime_type = "application/vnd.nextthought.webinarregistrationfields"


@WithRepr
@interface.implementer(IWebinarSession)
class WebinarSession(PersistentCreatedAndModifiedTimeObject,
                     SchemaConfigured):

    createDirectFieldProperties(IWebinarSession)

    mimeType = mime_type = "application/vnd.nextthought.webinarsession"


@interface.implementer(IUserWebinarAttendance)
class UserWebinarAttendance(PersistentCreatedAndModifiedTimeObject,
                            SchemaConfigured):

    createDirectFieldProperties(IUserWebinarAttendance)

    mimeType = mime_type = "application/vnd.nextthought.userwebinarattendance"


@WithRepr
@interface.implementer(IUserWebinarProgress)
class UserWebinarProgress(PersistentCreatedAndModifiedTimeObject,
                          Contained,
                          SchemaConfigured):
    createDirectFieldProperties(IUserWebinarProgress)

    __parent__ = None
    __name__ = None

    mimeType = mime_type = "application/vnd.nextthought.webinar.userprogress"


@WithRepr
@EqHash('webinarKey')
@interface.implementer(IWebinar, IAttributeAnnotatable)
class Webinar(PersistentCreatedAndModifiedTimeObject,
              SchemaConfigured):

    createDirectFieldProperties(IWebinar)

    mimeType = mime_type = "application/vnd.nextthought.webinar"

    sessions = alias('times')
    __parent__ = None

    @property
    def __name__(self):
        return str(self.webinarKey)

    @property
    def ntiid(self):
        # Let's us be linkable
        return to_external_ntiid_oid(self)


@interface.implementer(IWebinarCollection)
class WebinarCollection(SchemaConfigured):

    createDirectFieldProperties(IWebinarCollection)

    mimeType = mime_type = "application/vnd.nextthought.webinarcollection"


@WithRepr
@interface.implementer(IWebinarRegistrationMetadata)
class WebinarRegistrationMetadata(PersistentCreatedAndModifiedTimeObject,
                                  SchemaConfigured):
    """
    A :class:`IWebinarRegistration` object.
    """

    createDirectFieldProperties(IWebinarRegistrationMetadata)

    mimeType = mime_type = "application/vnd.nextthought.webinarregistrationmetadata"

    __parent__ = None
    creator = None

    @property
    def ntiid(self):
        # Let's us be linkable
        return to_external_ntiid_oid(self)
