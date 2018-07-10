#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: completion_views.py 127529 2018-03-23 15:45:39Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from zope import component

from nti.app.products.webinar import VIEW_UPCOMING_WEBINARS

from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.externalization.externalization import StandardExternalFields

from nti.externalization.interfaces import LocatedExternalDict

from nti.site.utils import unregisterUtility

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


@view_config(route_name='objects.generic.traversal',
             context=IWebinarAuthorizedIntegration,
             request_method='DELETE',
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class WebinarIntegrationDeleteView(AbstractAuthenticatedView):
    """
    Allow deleting (unauthorizing) a :class:`IWebinarAuthorizedIntegration`.
    """

    def __call__(self):
        registry = component.getSiteManager()
        unregisterUtility(registry, provided=IWebinarAuthorizedIntegration)
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             context=IWebinarAuthorizedIntegration,
             request_method='GET',
             name=VIEW_UPCOMING_WEBINARS,
             renderer='rest')
class UpcomingWebinarsView(AbstractAuthenticatedView):
    """
    Fetch the upcoming webinars for an :class:`IWebinarAuthorizedIntegration`.

    FIXME: permission
    permission=ACT_CONTENT_EDIT,
    """

    def __call__(self):
        client = component.queryMultiAdapter((self.context, self.request),
                                             IWebinarClient)
        webinars = client.get_upcoming_webinars()
        result = LocatedExternalDict()
        result[ITEMS] = webinars
        result[TOTAL] = result[ITEM_COUNT] = len(webinars)
        return result
