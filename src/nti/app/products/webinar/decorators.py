#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Externalization decorators.

.. $Id: decorators.py 122490 2017-09-29 03:36:57Z chris.utz $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.location.interfaces import ILocation

from nti.app.products.webinar import REL_AUTH_WEBINAR
from nti.app.products.webinar import VIEW_JOIN_WEBINAR
from nti.app.products.webinar import VIEW_RESOLVE_WEBINAR
from nti.app.products.webinar import VIEW_WEBINAR_REGISTER
from nti.app.products.webinar import VIEW_UPCOMING_WEBINARS
from nti.app.products.webinar import VIEW_WEBINAR_UNREGISTER
from nti.app.products.webinar import VIEW_WEBINAR_REGISTRATION_FIELDS

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IWebinarAuthorizedIntegration
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadataContainer

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_authorization import has_permission

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.dataserver.authorization import is_admin_or_site_admin

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.interfaces import ILinkExternalHrefOnly

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(IWebinarIntegration)
@interface.implementer(IExternalMappingDecorator)
class _WebinarAuthorizeDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, unused_result):
        return super(_WebinarAuthorizeDecorator, self)._predicate(context, unused_result) \
           and is_admin_or_site_admin(self.remoteUser)

    def _do_decorate_external(self, context, result):
        links = result.setdefault(LINKS, [])
        link = Link(context,
                    rel=REL_AUTH_WEBINAR,
                    elements=('@@%s' % REL_AUTH_WEBINAR,))
        interface.alsoProvides(link, ILocation)
        link.__name__ = ''
        link.__parent__ = context
        links.append(link)


@component.adapter(IWebinarAuthorizedIntegration)
@interface.implementer(IExternalMappingDecorator)
class _AuthorizedWebinarDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, unused_result):
        return super(_AuthorizedWebinarDecorator, self)._predicate(context, unused_result) \
           and has_permission(ACT_CONTENT_EDIT, context, self.request)

    def _do_decorate_external(self, context, result):
        links = result.setdefault(LINKS, [])
        for rel in (VIEW_RESOLVE_WEBINAR, VIEW_UPCOMING_WEBINARS):
            link = Link(context,
                        rel=rel,
                        elements=('@@%s' % rel,))
            interface.alsoProvides(link, ILocation)
            link.__name__ = ''
            link.__parent__ = context
            links.append(link)


@component.adapter(IWebinar)
@interface.implementer(IExternalMappingDecorator)
class _WebinarDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, unused_result):
        # The user could still join the webinar even if we do not
        # have an integration, but we could not get progress back.
        return super(_WebinarDecorator, self)._predicate(context, unused_result) \
           and has_permission(ACT_READ, context, self.request) \
           and IWebinarClient(context, None) is not None

    def is_registered(self, webinar):
        # pylint: disable=no-member
        reg_container = IWebinarRegistrationMetadataContainer(webinar)
        return self.remoteUser.username in reg_container

    def _do_decorate_external(self, context, result):
        links = result.setdefault(LINKS, [])
        if self.is_registered(context):
            rels = (VIEW_JOIN_WEBINAR, VIEW_WEBINAR_UNREGISTER)
        else:
            rels = (VIEW_WEBINAR_REGISTRATION_FIELDS, VIEW_WEBINAR_REGISTER)

        for rel in rels:
            link = Link(context,
                        rel=rel,
                        elements=('@@%s' % rel,))
            interface.alsoProvides(link, ILocation)
            link.__name__ = ''
            link.__parent__ = context
            links.append(link)

        if 'href' not in result:
            link = Link(context)
            interface.alsoProvides(link, ILinkExternalHrefOnly)
            result['href'] = link
