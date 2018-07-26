#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import assert_that

import unittest

from datetime import datetime
from datetime import timedelta

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarProgressContainer

from nti.app.products.webinar.progress import should_update_progress

from nti.app.products.webinar.tests import SharedConfiguringTestLayer

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
          "organizerKey": 111111111111,
          "webinarKey": 222222222222,
          "webinarID": u"web_id",
          "timeZone": u"tz",
          "registrationUrl": u"http://reg_url",
}

class TestWebinarProgress(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_progress(self):
        now = datetime.utcnow()
        sixty_seconds_ago = now - timedelta(seconds=60)
        thirty_seconds_ago = now - timedelta(seconds=30)
        thirty_seconds_later = now + timedelta(seconds=30)
        one_day_later = now + timedelta(days=1)

        # Future webinar
        webinar = IWebinar(dict(webinar_json))
        webinar.times[0].endTime = one_day_later
        assert_that(should_update_progress(webinar), is_(False))

        # Completed webinar
        webinar = IWebinar(dict(webinar_json))
        webinar.times[0].endTime = thirty_seconds_ago
        container = IWebinarProgressContainer(webinar)
        assert_that(container.last_updated, none())

        # First time
        assert_that(should_update_progress(webinar), is_(True))

        # Updated in past
        container.last_updated = sixty_seconds_ago
        assert_that(should_update_progress(webinar), is_(True))

        # Just updated
        container.last_updated = thirty_seconds_later
        assert_that(should_update_progress(webinar), is_(False))

        # Updated a day ago
        container.last_updated = one_day_later
        assert_that(should_update_progress(webinar), is_(False))

        # Backing off updates
        webinar.times[0].endTime = now - timedelta(hours=6)
        container.last_updated = now - timedelta(hours=5)
        assert_that(should_update_progress(webinar), is_(True))
