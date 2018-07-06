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

from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration

from nti.appserver.ugd_edit_views import UGDDeleteView

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.site.utils import unregisterUtility

logger = __import__('logging').getLogger(__name__)


@view_config(route_name='objects.generic.traversal',
             context=IWebinarAuthorizedIntegration,
             request_method='DELETE',
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class WebinarIntegrationDeleteView(UGDDeleteView):
    """
    Allow deleting (unauthorizing) a :class:`IWebinarAuthorizedIntegration`.
    """

    def __call__(self):
        registry = component.getSiteManager()
        unregisterUtility(registry, provided=IWebinarAuthorizedIntegration)
        return hexc.HTTPNoContent()
