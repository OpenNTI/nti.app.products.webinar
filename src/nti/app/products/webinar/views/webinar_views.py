#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: completion_views.py 127529 2018-03-23 15:45:39Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.event import notify

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.webinar import VIEW_JOIN_WEBINAR
from nti.app.products.webinar import VIEW_RESOLVE_WEBINAR
from nti.app.products.webinar import VIEW_WEBINAR_REGISTER
from nti.app.products.webinar import VIEW_UPCOMING_WEBINARS
from nti.app.products.webinar import VIEW_WEBINAR_REGISTRATION_FIELDS

from nti.app.products.webinar import MessageFactory as _

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import JoinWebinarEvent
from nti.app.products.webinar.interfaces import WebinarRegistrationError
from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadataContainer

from nti.app.products.webinar.utils import raise_error

from nti.dataserver.authorization import ACT_READ
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
class ResolveWebinarsView(UpcomingWebinarsView):
    """
    Fetch the upcoming webinar for a given filter url or webinarKey. Through
    the UI, a registration URL will give the user an option of available
    webinars to choose from; we mimic that here by returning all the possible
    webinars if a registrationUrl is given.
    """

    def get_webinar_param(self):
        values = self.request.params
        result = CaseInsensitiveDict(values)
        return result.get('webinar') \
            or result.get('webinar_key') \
            or result.get('key') \
            or result.get('webinar_url')

    def filter_webinars(self, webinars, include_filter):
        """
        Include anything matching on webinarKey or registrationUrl.
        """
        return [x for x in webinars
                if x.webinarKey == include_filter \
                or x.registrationUrl == include_filter]

    def __call__(self):
        webinar_filter = self.get_webinar_param()
        if not webinar_filter:
            raise_error({'message': _(u"Must supply webinar key."),
                         'code': 'MissingWebinarURLError'})
        result = super(ResolveWebinarsView, self).__call__()
        result[ITEMS] = self.filter_webinars(result[ITEMS],
                                             webinar_filter)
        result[ITEM_COUNT] = len(result[ITEMS])
        return result


@view_config(route_name='objects.generic.traversal',
             context=IWebinar,
             request_method='GET',
             name=VIEW_WEBINAR_REGISTRATION_FIELDS,
             permission=ACT_READ,
             renderer='rest')
class WebinarRegistrationFieldView(AbstractAuthenticatedView):
    """
    Fetch the :class:`IWebinarRegistrationFields` for the contextual
    :class:`IWebinar` object.
    """

    def __call__(self):
        client = component.queryMultiAdapter((self.context, self.request),
                                             IWebinarClient)
        result = client.get_registration_fields(self.context.webinarKey)
        if not result:
            raise_error({'message': _(u"Webinar does not exist."),
                         'code': 'WebinarNotFoundError'},
                        factory=hexc.HTTPNotFound)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IWebinar,
             request_method='POST',
             name=VIEW_WEBINAR_REGISTER,
             permission=ACT_READ,
             renderer='rest')
class WebinarRegisterView(AbstractAuthenticatedView,
                          ModeledContentUploadRequestUtilsMixin):
    """
    Allows the user to register for the contextual
    :class:`IWebinar` object.
    """

    def __call__(self):
        registration_data = self.readInput()
        if not registration_data:
            raise_error({'message': _(u"Must supply registration information."),
                         'code': 'RegistrationDataNotFoundError'})
        client = component.queryMultiAdapter((self.context, self.request),
                                             IWebinarClient)
        try:
            registration_metadata = client.register_user(self.remoteUser,
                                                         self.context.webinarKey,
                                                         registration_data)
        except WebinarRegistrationError as validation_error:
            logger.info('Validation error during registration (%s) (%s)',
                        self.remoteUser.username,
                        validation_error.json)
            raise_error({'message': _(u"Validation error during registration."),
                         'code': 'WebinarRegistrationValidationError',
                         'error_dict': validation_error.json},
                        factory=hexc.HTTPUnprocessableEntity)
        logger.info('Registered user for webinar (%s) (%s) (%s)',
                    self.context.webinarKey,
                    self.remoteUser,
                    registration_metadata)
        container = IWebinarRegistrationMetadataContainer(self.context)
        if self.remoteUser.username not in container:
            container[self.remoteUser.username] = registration_metadata
        return container[self.remoteUser.username]


@view_config(route_name='objects.generic.traversal',
             context=IWebinar,
             request_method='GET',
             name=VIEW_JOIN_WEBINAR,
             permission=ACT_READ,
             renderer='rest')
class JoinWebinarView(AbstractAuthenticatedView):
    """
    Allows the user to join the contextual :class:`IWebinar` object.
    """

    def __call__(self):
        container = IWebinarRegistrationMetadataContainer(self.context)
        if self.remoteUser.username not in container:
            # XXX: What do we do here?
            raise_error({'message': _(u"Webinar registration does not exist."),
                         'code': 'WebinarRegistrationNotFoundError'},
                        factory=hexc.HTTPNotFound)
        registration_metadata = container[self.remoteUser.username]
        notify(JoinWebinarEvent(user=self.remoteUser,
                                webinar=self.context,
                                timestamp=datetime.utcnow()))
        self.request.environ['nti.request_had_transaction_side_effects'] = 'True'
        raise hexc.HTTPSeeOther(location=registration_metadata.join_url)
