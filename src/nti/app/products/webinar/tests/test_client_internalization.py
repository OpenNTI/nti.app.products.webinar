#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import os
import unittest
import simplejson

from nti.testing.matchers import verifiably_provides

from nti.externalization.externalization import to_external_object

from nti.app.products.webinar.tests import SharedConfiguringTestLayer

from nti.app.products.webinar.interfaces import IWebinar
from nti.app.products.webinar.interfaces import IWebinarField
from nti.app.products.webinar.interfaces import IWebinarSession
from nti.app.products.webinar.interfaces import IWebinarQuestion
from nti.app.products.webinar.interfaces import IWebinarCollection
from nti.app.products.webinar.interfaces import IWebinarQuestionAnswer
from nti.app.products.webinar.interfaces import IWebinarRegistrationMetadata
from nti.app.products.webinar.interfaces import IWebinarRegistrationFields

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

metadata_json = {
          "organizer_key": u"111111111111",
          "webinar_key": u"222222222222",
          "registrant_key": u"reg_key",
          "join_url": u"http://reg_url",
          "creator": "creator"
}


class TestWebinarClientInternalization(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _load_resource(self, name):
        path = os.path.join(os.path.dirname(__file__), name)
        with open(path, "r") as fp:
            source = simplejson.loads(fp.read())
        return source

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
        assert_that(webinar.organizerKey, is_("111111111111"))
        assert_that(webinar.registrationUrl, is_('http://reg_url'))
        assert_that(webinar.webinarID, is_('web_id'))
        assert_that(webinar.webinarKey, is_("222222222222"))

        collection_ext = to_external_object(collection)
        assert_that(collection_ext['webinars'], has_length(1))
        assert_that(collection_ext['webinars'][0]['times'], has_length(1))

    def test_webinar_registration(self):
        registration_data = self._load_resource('fields.json')
        fields = IWebinarRegistrationFields(registration_data)
        assert_that(fields, verifiably_provides(IWebinarRegistrationFields))
        assert_that(fields.fields, has_length(16))
        assert_that(fields.questions, has_length(4))

        for field in fields.fields:
            assert_that(field, verifiably_provides(IWebinarField))

        for question in fields.questions:
            assert_that(question, verifiably_provides(IWebinarQuestion))
            if question.type == 'multipleChoice':
                assert_that(question.answers, has_length(2))
                for question_answer in question.answers:
                    assert_that(question_answer,
                                verifiably_provides(IWebinarQuestionAnswer))

    def test_webinar_registration_metadata(self):
        metadata = IWebinarRegistrationMetadata(metadata_json)
        assert_that(metadata, verifiably_provides(IWebinarRegistrationMetadata))
        assert_that(metadata.organizer_key, is_("111111111111"))
        assert_that(metadata.join_url, is_('http://reg_url'))
        assert_that(metadata.registrant_key, is_('reg_key'))
        assert_that(metadata.webinar_key, is_("222222222222"))
