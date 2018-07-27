#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarSession

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IInternalObjectUpdater)
class WebinarUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IWebinar

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        # We need these to be unicode or we may have rounding issues
        for key in ('organizerKey', 'webinarKey'):
            parsed[key] = unicode(parsed[key])
        if 'registrationUrl' in parsed and not parsed['registrationUrl']:
            parsed['registrationUrl'] = None
        parsed['times'] = [IWebinarSession(x) for x in parsed.get('times') or ()]
        return super(WebinarUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
