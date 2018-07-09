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

from nti.app.products.integration.interfaces import IIntegrationCollectionProvider

from nti.app.products.integration.integration import AbstractIntegration
from nti.app.products.integration.integration import AbstractOAuthAuthorizedIntegration

from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IWebinarIntegration)
class GoToWebinarIntegration(AbstractIntegration,
                             SchemaConfigured):

    createDirectFieldProperties(IWebinarIntegration)

    __name__ = 'webinar'

    mimeType = mime_type = "application/vnd.nextthought.integration.gotowebinarintegration"


@WithRepr
@interface.implementer(IGoToWebinarAuthorizedIntegration)
class GoToWebinarAuthorizedIntegration(AbstractOAuthAuthorizedIntegration,
                                       PersistentCreatedAndModifiedTimeObject,
                                       SchemaConfigured):

    createDirectFieldProperties(IGoToWebinarAuthorizedIntegration)

    __name__ = 'webinar'

    mimeType = mime_type = "application/vnd.nextthought.integration.gotowebinarauthorizedintegration"

    def get_access_token(self):
        # FIXME: implement
        pass


@interface.implementer(IIntegrationCollectionProvider)
class WebinarIntegrationProvider(object):

    def get_collection_iter(self):
        """
        Return our authorized integration if we have it, otherwise, return an
        an :class:`IIntegration` object that can be used for authorizing.
        """
        result = component.queryUtility(IWebinarAuthorizedIntegration)
        if result is None:
            result = GoToWebinarIntegration(title=u'Integrate with GOTOWebinar')
        return (result,)

