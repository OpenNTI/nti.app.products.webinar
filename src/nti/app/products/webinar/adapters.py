# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation.interfaces import IAnnotations

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadataContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.traversal.traversal import find_interface


WEBINAR_REGISTRATION_CONTAINER_KEY = 'nti.app.products.webinar.interfaces.IWebinarRegistrationContainer'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IGoToWebinarAuthorizedIntegration)
@component.adapter(IWebinar)
def webinar_to_auth_integration(unused_webinar):
    """
    Return registered utility. When we have to be smarter, we will need to
    check organizerKey etc.
    """
    return component.queryUtility(IGoToWebinarAuthorizedIntegration)


@interface.implementer(IWebinarClient)
@component.adapter(IWebinar, IRequest)
def webinar_to_client(webinar, request):
    auth_integration = IGoToWebinarAuthorizedIntegration(webinar)
    return component.queryMultiAdapter((auth_integration, request),
                                        IWebinarClient)


@component.adapter(IWebinar)
@interface.implementer(IWebinarRegistrationMetadataContainer)
class WebinarRegistrationMetadataContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                   SchemaConfigured):
    """
    Stores :class:`IWebinarRegistration` objects.
    """
    createDirectFieldProperties(IWebinarRegistrationMetadataContainer)


def WebinarRegistrationMetadataContainerFactory(webinar):
    result = None
    annotations = IAnnotations(webinar)
    KEY = WEBINAR_REGISTRATION_CONTAINER_KEY
    try:
        result = annotations[KEY]
    except KeyError:
        result = WebinarRegistrationMetadataContainer()
        annotations[KEY] = result
        result.__name__ = KEY
        result.__parent__ = webinar
        IConnection(webinar).add(result)
    return result


def webinar_to_course(webinar):
    return find_interface(webinar, ICourseInstance)
