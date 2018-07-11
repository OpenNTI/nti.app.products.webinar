#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

from zope import component
from zope import interface

from nti.app.products.integration.interfaces import IIntegrationCollectionProvider

from nti.app.products.integration.integration import AbstractIntegration
from nti.app.products.integration.integration import AbstractOAuthAuthorizedIntegration

from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.internalization import update_from_external_object

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IWebinarIntegration)
class GoToWebinarIntegration(AbstractIntegration,
                             SchemaConfigured):

    createDirectFieldProperties(IWebinarIntegration)

    __name__ = u'webinar'

    mimeType = mime_type = "application/vnd.nextthought.integration.gotowebinarintegration"


@component.adapter(dict)
@interface.implementer(IGoToWebinarAuthorizedIntegration)
def _auth_webinar_factory(access_data):
    """
    On successful authorization, we get a dict back of auth info.
    """
    real_name = '%s %s' % (access_data.get('firstName'),
                           access_data.get('lastName'))
    access_data['webinar_realname'] = real_name
    access_data['webinar_email'] = access_data.get('email')
    access_data['authorization_date'] = datetime.utcnow()
    obj = GoToWebinarAuthorizedIntegration()
    # We exclude this field from externalization so it does not get picked
    # up on internalization either; we must manually set it here.
    obj.refresh_token = access_data['refresh_token']
    update_from_external_object(obj, access_data)
    return obj


@WithRepr
@interface.implementer(IGoToWebinarAuthorizedIntegration)
class GoToWebinarAuthorizedIntegration(AbstractOAuthAuthorizedIntegration,
                                       PersistentCreatedAndModifiedTimeObject,
                                       SchemaConfigured):

    createDirectFieldProperties(IGoToWebinarAuthorizedIntegration)

    __name__ = u'webinar'

    mimeType = mime_type = "application/vnd.nextthought.integration.gotowebinarauthorizedintegration"
    title = u'Authorized GOTOWebinar Integration'


@interface.implementer(IIntegrationCollectionProvider)
class WebinarIntegrationProvider(object):

    def get_collection_iter(self):
        """
        Return our authorized integration if we have it, otherwise, return an
        an :class:`IIntegration` object that can be used for authorizing.
        """
        result = component.queryUtility(IGoToWebinarAuthorizedIntegration)
        if result is None:
            result = GoToWebinarIntegration(title=u'Integrate with GOTOWebinar')
        return (result,)

