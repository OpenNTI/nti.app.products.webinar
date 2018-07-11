#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.cachedescriptors.property import readproperty

from nti.app.products.webinar.interfaces import IWebinarAsset

from nti.contenttypes.presentation.mixins import PersistentPresentationAsset

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IWebinarAsset)
class WebinarAsset(PersistentPresentationAsset):

    createDirectFieldProperties(IWebinarAsset)
    mimeType = mime_type = 'application/vnd.nextthought.webinarasset'
    __external_class_name__ = "WebinarAsset"

    Creator = alias('creator')
    desc = alias('description')
    __name__ = alias('ntiid')

    @readproperty
    def ntiid(self):
        return to_external_ntiid_oid(self)
