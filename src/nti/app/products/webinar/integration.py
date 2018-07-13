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

from zope.intid.interfaces import IIntIds

from nti.app.products.integration.interfaces import IIntegrationCollectionProvider

from nti.app.products.integration.integration import AbstractIntegration
from nti.app.products.integration.integration import AbstractOAuthAuthorizedIntegration

from nti.app.products.webinar.interfaces import IWebinarIntegration
from nti.app.products.webinar.interfaces import IGoToWebinarAuthorizedIntegration

from nti.app.products.webinar.utils import get_auth_tokens

from nti.dataserver.interfaces import IRedisClient

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

    lock_timeout = 60 * 3
    # 2 hours for access token
    access_token_expiry = 60 * 120
    # 60 days for refresh token
    refresh_token_expiry = 60 * 60 * 24 * 60

    @property
    def _key_base_name(self):
        intids = component.getUtility(IIntIds)
        intid = intids.getId(self)
        return 'webinar/tokens/%s/%s/%s' % (self.account_key, self.organizer_key, intid)

    @property
    def _access_token_key_name(self):
        return '%s/%s' % (self._key_base_name, 'access_token')

    @property
    def _refresh_token_key_name(self):
        return '%s/%s' % (self._key_base_name, 'refresh_token')

    def store_tokens(self, access_token, refresh_token):
        """
        Called after initialization or during update, stores the state of the
        tokens. This should only be called with appropriate safeguarding of
        concurrency.
        """
        self._redis_client.setex(self._access_token_key_name,
                                 value=access_token,
                                 time=self.access_token_expiry)
        self._redis_client.setex(self._refresh_token_key_name,
                                 value=refresh_token,
                                 time=self.refresh_token_expiry)

    @property
    def _redis_client(self):
        return component.getUtility(IRedisClient)

    @property
    def access_token(self):
        result = self._redis_client.get(self._access_token_key_name)
        if result is None:
            result = self.update_tokens()
        return result

    def get_access_token(self):
        return self.access_token

    @property
    def refresh_token(self):
        # This should never be None
        return self._redis_client.get(self._refresh_token_key_name)

    def get_refresh_token(self):
        return self.refresh_token

    @property
    def _lock(self):
        return self._redis_client.lock(self._key_base_name,
                                       self.lock_timeout)

    def update_tokens(self, old_access_token=None):
        with self._lock:
            # Someone may beat us; if so, user their new token
            current_access_token = self._redis_client.get(self._access_token_key_name)
            if     not current_access_token \
                or current_access_token == old_access_token:
                # First one here, update and store
                access_token, refresh_token = get_auth_tokens(self.refresh_token)
                self.store_tokens(access_token, refresh_token)
                result = access_token
            else:
                result = current_access_token
        return result


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

