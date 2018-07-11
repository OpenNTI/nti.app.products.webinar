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

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarSession
from nti.app.products.webinar.interfaces import IWebinarCollection

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.internalization import update_from_external_object

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@component.adapter(dict)
@interface.implementer(IWebinar)
def _webinar_factory(ext):
    obj = Webinar()
    ext['times'] = [IWebinarSession(x) for x in ext['times'] or ()]
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


@interface.implementer(IWebinarSession)
class WebinarSession(PersistentCreatedAndModifiedTimeObject,
                     SchemaConfigured):

    createDirectFieldProperties(IWebinarSession)

    mimeType = mime_type = "application/vnd.nextthought.webinarsession"


@interface.implementer(IWebinar)
class Webinar(PersistentCreatedAndModifiedTimeObject,
              SchemaConfigured):

    createDirectFieldProperties(IWebinar)

    mimeType = mime_type = "application/vnd.nextthought.webinar"

    sessions = alias('times')
    __parent__ = None

    @property
    def __name__(self):
        return str(self.webinarKey)


@interface.implementer(IWebinarCollection)
class WebinarCollection(SchemaConfigured):

    createDirectFieldProperties(IWebinarCollection)

    mimeType = mime_type = "application/vnd.nextthought.webinarcollection"

