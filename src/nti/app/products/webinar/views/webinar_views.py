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

from requests.structures import CaseInsensitiveDict

from zope import component

from nti.app.products.webinar import VIEW_RESOLVE_WEBINAR
from nti.app.products.webinar import VIEW_UPCOMING_WEBINARS

from nti.app.products.webinar import MessageFactory as _

from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar.utils import raise_error

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
             context=IGoToWebinarAuthorizedIntegration,
             request_method='DELETE',
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class GoToWebinarIntegrationDeleteView(AbstractAuthenticatedView):
    """
    Allow deleting (unauthorizing) a :class:`IWebinarAuthorizedIntegration`.
    """

    def __call__(self):
        registry = component.getSiteManager()
        unregisterUtility(registry, provided=IGoToWebinarAuthorizedIntegration)
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             context=IWebinarAuthorizedIntegration,
             request_method='GET',
             name=VIEW_UPCOMING_WEBINARS,
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class UpcomingWebinarsView(AbstractAuthenticatedView):
    """
    Fetch the upcoming webinars for an :class:`IWebinarAuthorizedIntegration`.
    """

    def __call__(self):
        client = component.queryMultiAdapter((self.context, self.request),
                                             IWebinarClient)
        webinars = client.get_upcoming_webinars()
        result = LocatedExternalDict()
        result[ITEMS] = webinars
        result[TOTAL] = result[ITEM_COUNT] = len(webinars)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IWebinarAuthorizedIntegration,
             request_method='GET',
             name=VIEW_RESOLVE_WEBINAR,
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class ResolveWebinarView(AbstractAuthenticatedView):
    """
    Fetch the upcoming webinars for an :class:`IWebinarAuthorizedIntegration`.
    """

    def get_webinar_param(self):
        values = self.request.params
        result = CaseInsensitiveDict(values)
        return result.get('webinar') \
            or result.get('webinar_key') \
            or result.get('key') \
            or result.get('webinar_url')

    def get_webinar_key(self, webinar_param):
        """
        We may have a url or a key here. The trailing part of the registration
        url is the webinar key.

        e.g. https://attendee.gotowebinar.com/register/2665275951356935169
        """
        if not webinar_param:
            return
        if webinar_param.endswith('/'):
            webinar_param = webinar_param[:-1]
        return webinar_param.rsplit('/')[-1]

    def __call__(self):
        webinar_param = self.get_webinar_param()
        webinar_key = self.get_webinar_key(webinar_param)
        if not webinar_key:
            raise_error({'message': _(u"Must supply webinar key."),
                         'code': 'MissingWebinarURLError'})
        client = component.queryMultiAdapter((self.context, self.request),
                                             IWebinarClient)
        result = client.get_webinar(webinar_key)
        if not result:
            raise_error({'message': _(u"Cannot resolve webinar for given key."),
                         'code': 'CannotResolveWebinarError'},
                        factory=hexc.HTTPNotFound)
        return result
