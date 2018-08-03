# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation.interfaces import IAnnotations

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadataContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured


WEBINAR_REGISTRATION_CONTAINER_KEY = 'nti.app.products.webinar.interfaces.IWebinarRegistrationContainer'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IGoToWebinarAuthorizedIntegration)
@component.adapter(IWebinar)
def webinar_to_auth_integration(webinar):
    """
    Return registered utility, but only if the organizer key matches. The
    alternative indicates webinar in un-maintable states.
    """
    result = component.queryUtility(IGoToWebinarAuthorizedIntegration)
    if result is not None and webinar.organizerKey == result.organizer_key:
        return result


@interface.implementer(IWebinarClient)
@component.adapter(IWebinar)
def webinar_to_client(webinar):
    auth_integration = IGoToWebinarAuthorizedIntegration(webinar, None)
    return IWebinarClient(auth_integration, None)


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
