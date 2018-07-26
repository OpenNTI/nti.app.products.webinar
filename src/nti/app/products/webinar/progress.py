#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation import IAnnotations

from zope.container.contained import Contained

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IUserWebinarProgress
from nti.app.products.webinar.interfaces import IWebinarProgressContainer
from nti.app.products.webinar.interfaces import IUserWebinarProgressContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IUser

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

WEBINAR_PROGRESS_CONTAINER_KEY = 'nti.app.products.webinar.interfaces.IUserWebinarProgress'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IUserWebinarProgressContainer)
class UserWebinarProgressContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                   SchemaConfigured):
    createDirectFieldProperties(IUserWebinarProgressContainer)

    __parent__ = None
    __name__ = None


@interface.implementer(IWebinarProgressContainer)
class WebinarProgressContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                             SchemaConfigured):
    createDirectFieldProperties(IWebinarProgressContainer)


def webinar_to_webinar_progress_container(webinar):
    annotations = IAnnotations(webinar)
    result = annotations.get(WEBINAR_PROGRESS_CONTAINER_KEY)
    if result is None:
        result = WebinarProgressContainer()
        result.__parent__ = webinar
        result.__name__ = WEBINAR_PROGRESS_CONTAINER_KEY
        annotations[WEBINAR_PROGRESS_CONTAINER_KEY] = result
        IConnection(result).add(result)
    return result


@component.adapter(IUser, IWebinar)
@interface.implementer(IUserWebinarProgressContainer)
def _context_to_principal_container(user, webinar):
    container = IWebinarProgressContainer(webinar)
    try:
        result = container[user.username]
    except KeyError:
        result = UserWebinarProgressContainer()
        container[user.username] = result
    return result
