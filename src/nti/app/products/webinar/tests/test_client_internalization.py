#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.testing.matchers import verifiably_provides

from nti.externalization.externalization import to_external_object

from nti.app.products.webinar.tests import SharedConfiguringTestLayer

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarSession
from nti.app.products.webinar.interfaces import IWebinarCollection

webinar_json = {
          "numberOfRegistrants": 0,
          "times": [
            {
              "startTime": u"2018-07-09T17:00:00Z",
              "endTime": u"2018-07-09T18:00:00Z"
            }
          ],
          "description": u"desc",
          "subject": u"subject",
          "inSession": True,
          "organizerKey": 0,
          "webinarKey": 0,
          "webinarID": u"web_id",
          "timeZone": u"tz",
          "registrationUrl": u"reg_url",
}


class TestWebinarClientInternalization(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_webinars(self):
        webinar_container_ext = [webinar_json,]
        collection = IWebinarCollection(webinar_container_ext)
        assert_that(collection, verifiably_provides(IWebinarCollection))
        assert_that(collection.webinars, has_length(1))
        webinar = collection.webinars[0]
        assert_that(webinar, verifiably_provides(IWebinar))
        assert_that(webinar.times, has_length(1))
        session = webinar.times[0]
        assert_that(session, verifiably_provides(IWebinarSession))

        assert_that(webinar.description, is_('desc'))
        assert_that(webinar.inSession, is_(True))
        assert_that(webinar.numberOfRegistrants, is_(0))
        assert_that(webinar.timeZone, is_('tz'))
        assert_that(webinar.subject, is_('subject'))
        assert_that(webinar.organizerKey, is_(0))
        assert_that(webinar.registrationUrl, is_('reg_url'))
        assert_that(webinar.webinarID, is_('web_id'))
        assert_that(webinar.webinarKey, is_(0))


        collection_ext = to_external_object(collection)
        assert_that(collection_ext['webinars'], has_length(1))
        assert_that(collection_ext['webinars'][0]['times'], has_length(1))
