#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned


from nti.app.products.integration.interfaces import IIntegration
from nti.app.products.integration.interfaces import IOAuthAuthorizedIntegration

from nti.schema.field import DecodingValidTextLine as ValidTextLine


class IWebinarIntegration(IIntegration):
    """
    A webinar integration
    """


class IWebinarAuthorizedIntegration(IOAuthAuthorizedIntegration,
                                    IWebinarIntegration):
    """
    An :class:`IOAuthAuthorizedIntegration` for webinars.
    """


class IGoToWebinarAuthorizedIntegration(IWebinarAuthorizedIntegration):
    """
    An :class:`IOAuthAuthorizedIntegration` for GOTO webinars.
    """

    organizer_key = ValidTextLine(title=u"GOTOWebinar organizer key",
                                  required=True)

    account_key = ValidTextLine(title=u"GOTOWebinar account key",
                                required=True)
