#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime
from dateutil import tz
import requests

from nectarclient_lib import base
from nectarclient_lib.tests.unit import fakes
from nectarclient_lib.tests.unit import utils


def create_response_obj_with_header():
    resp = requests.Response()
    resp.headers['x-openstack-request-id'] = fakes.FAKE_REQUEST_ID
    return resp


def create_response_obj_with_compute_header():
    resp = requests.Response()
    resp.headers['x-compute-request-id'] = fakes.FAKE_REQUEST_ID
    return resp


class BaseTest(utils.TestCase):
    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual("<Resource baz=spam, foo=bar>", repr(r))

    def test_getid(self):
        self.assertEqual(4, base.getid(4))

        class TmpObject:
            id = 4

        self.assertEqual(4, base.getid(TmpObject))

    def test_eq(self):
        # Two resources of the same type with the same id: equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertEqual(r1, r2)

        # Two resources of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = fakes.FakeResource(None, {'id': 1})
        self.assertNotEqual(r1, r2)

        # Two resources with no ID: equal if their info is equal
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertEqual(r1, r2)

    def test_ne(self):
        # Two resources of different types: never equal
        r1 = base.Resource(None, {'id': 1, 'name': 'test'})
        r2 = object()
        self.assertNotEqual(r1, r2)

    def test_resource_object_with_request_ids(self):
        resp_obj = create_response_obj_with_header()
        r = base.Resource(None, {"name": "1"}, resp=resp_obj)
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, r.request_ids)

    def test_resource_object_with_compute_request_ids(self):
        resp_obj = create_response_obj_with_compute_header()
        r = base.Resource(None, {"name": "1"}, resp=resp_obj)
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, r.request_ids)

    def test_resource_object_with_datetime(self):
        r = fakes.DTResource(
            None, {"name": "1", "datetime": "2022-08-23T00:00:00"}
        )
        self.assertEqual(datetime.datetime(2022, 8, 23, 0, 0), r.datetime)

    def test_resource_object_with_date(self):
        r = fakes.DTResource(None, {"name": "1", "datetime": "2022-08-23"})
        self.assertEqual(datetime.datetime(2022, 8, 23, 0, 0), r.datetime)

    def test_resource_object_with_datetime_with_tz(self):
        r = fakes.DTResource(
            None, {"name": "1", "datetime": "2022-08-23T00:00:00+00:00"}
        )

        dt = datetime.datetime(2022, 8, 23, 0, 0, tzinfo=tz.UTC)
        self.assertEqual(dt, r.datetime)
        self.assertEqual(tz.gettz(), r.datetime.tzinfo)

    def test_resource_object_with_datetime_unknown_format(self):
        r = fakes.DTResource(
            None, {"name": "1", "datetime": "2022-08-23 00:00:00+00:00"}
        )
        self.assertEqual("2022-08-23 00:00:00+00:00", r.datetime)


class ListWithMetaTest(utils.TestCase):
    def test_list_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.ListWithMeta([], resp)
        self.assertEqual([], obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class DictWithMetaTest(utils.TestCase):
    def test_dict_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.DictWithMeta({}, resp)
        self.assertEqual({}, obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class TupleWithMetaTest(utils.TestCase):
    def test_tuple_with_meta(self):
        resp = create_response_obj_with_header()
        expected_tuple = (1, 2)
        obj = base.TupleWithMeta(expected_tuple, resp)
        self.assertEqual(expected_tuple, obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class StrWithMetaTest(utils.TestCase):
    def test_str_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.StrWithMeta("test-str", resp)
        self.assertEqual("test-str", obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)


class BytesWithMetaTest(utils.TestCase):
    def test_bytes_with_meta(self):
        resp = create_response_obj_with_header()
        obj = base.BytesWithMeta(b'test-bytes', resp)
        self.assertEqual(b'test-bytes', obj)
        # Check request_ids attribute is added to obj
        self.assertTrue(hasattr(obj, 'request_ids'))
        self.assertEqual(fakes.FAKE_REQUEST_ID_LIST, obj.request_ids)
