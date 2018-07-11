#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: internalization.py 129487 2018-06-04 15:11:07Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.app.products.webinar.interfaces import IWebinarAsset

logger = __import__('logging').getLogger(__name__)


@component.adapter(IWebinarAsset)
@interface.implementer(IInternalObjectUpdater)
class _WebinarAssetUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IWebinarAsset

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        result = super(_WebinarAssetUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
        self._ext_self.webinar.__parent__ = self._ext_self
        return result
