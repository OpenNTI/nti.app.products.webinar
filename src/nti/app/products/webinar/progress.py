#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation import IAnnotations

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarClient
from nti.app.products.webinar.interfaces import IWebinarProgressContainer
from nti.app.products.webinar.interfaces import IUserWebinarProgressContainer
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadataContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IUser

from nti.dataserver.users import User

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

WEBINAR_PROGRESS_CONTAINER_KEY = 'nti.app.products.webinar.interfaces.IUserWebinarProgress'

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IUserWebinarProgressContainer)
class UserWebinarProgressContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                   SchemaConfigured):
    createDirectFieldProperties(IUserWebinarProgressContainer)

    __parent__ = None
    __name__ = None


@interface.implementer(IWebinarProgressContainer)
class WebinarProgressContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                               SchemaConfigured):
    createDirectFieldProperties(IWebinarProgressContainer)


def webinar_to_webinar_progress_container(webinar):
    annotations = IAnnotations(webinar)
    result = annotations.get(WEBINAR_PROGRESS_CONTAINER_KEY)
    if result is None:
        result = WebinarProgressContainer()
        result.__parent__ = webinar
        result.__name__ = WEBINAR_PROGRESS_CONTAINER_KEY
        annotations[WEBINAR_PROGRESS_CONTAINER_KEY] = result
        # Test safety
        connection = IConnection(result, None)
        if connection is not None:
            connection.add(result)
    return result


@component.adapter(IUser, IWebinar)
@interface.implementer(IUserWebinarProgressContainer)
def _webinar_to_user_container(user, webinar):
    container = IWebinarProgressContainer(webinar)
    try:
        result = container[user.username]
    except KeyError:
        result = UserWebinarProgressContainer()
        container[user.username] = result
    return result


def update_webinar_progress(webinar):
    """
    Update the webinar progress for all of our registered users.
    """
    client = IWebinarClient(webinar, None)
    if client is None:
        logger.info("Cannot update webinar (%s) since we cannot obtain a client (unauthorized)",
                    webinar)
        return
    # Get the progress and store by registrantKey
    progress_collection = client.get_webinar_progress(webinar.webinarKey)
    registrant_key_to_progress = dict()
    for progress in progress_collection or ():
        registrant_progress = registrant_key_to_progress.setdefault(progress.registrantKey, [])
        registrant_progress.append(progress)

    # Store progress in our user container
    registration_container = IWebinarRegistrationMetadataContainer(webinar)
    for username, user_reg in registration_container.items():
        user = User.get_user(username)
        if user is None:
            continue
        user_container = component.queryMultiAdapter((user, webinar),
                                                     IUserWebinarProgressContainer)
        user_progress_objs = registrant_key_to_progress.get(user_reg.registrant_key)
        for user_progress in user_progress_objs or ():
            # XXX Is this what we want? Would we ever need to update an
            # existing record?
            if user_progress.sessionKey not in user_container:
                user_container[user_progress.sessionKey] = user_progress

    progress_container = IWebinarProgressContainer(webinar)
    progress_container.last_updated = datetime.utcnow()


def should_update_progress(webinar):
    """
    Decide whether we should fetch and pull progress information. We want to
    only do this periodically. Ideally, once one of the webinar session ends,
    then after 1 hr, 4 hrs, 16 hrs.
    """
    now = datetime.utcnow()
    last_session = None
    # Loop through until we get the most recently completed session
    for webinar_time in webinar.times:
        if webinar_time.endTime > now:
            break
        else:
            last_session = webinar_time
    result = False
    if last_session is not None:
        progress_container = IWebinarProgressContainer(webinar)
        if progress_container.last_updated is None:
            # First time update
            result = True
        else:
            update_delta = progress_container.last_updated - last_session.endTime
            since_end_delta = now - last_session.endTime
            if update_delta.total_seconds() < 0:
                # A new session finished
                result = True
            elif update_delta.days > 0:
                # Should not have to update after a day right...
                result = False
            elif since_end_delta.seconds < 3600:
                # Do not update more than once in first hour
                result = False
            else:
                # Ok, we've updated this session, but how long ago?
                # We'd like to update every so often, backing off.
                # e.g. 1x, 4 hrs later, 16 hrs later
                since_update_delta = now - progress_container.last_updated
                result = since_update_delta.seconds > update_delta.seconds * 4
    return result
