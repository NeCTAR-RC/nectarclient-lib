#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import abc
import copy
from datetime import datetime
import json
import logging

from dateutil import tz
from requests import Response

from nectarclient_lib import exceptions


LOCAL_TIMEZONE = tz.gettz()
LOG = logging.getLogger('__name__')


def getid(obj):
    """Get obj's id or object itself if no id
    Abstracts the common pattern of allowing both an object or
    an object's ID as a parameter when dealing with relationships.
    """
    try:
        return obj.id
    except AttributeError:
        return obj


class Manager(object):
    """Interacts with type of API
    Managers interact with a particular type of API (instances, types, etc.)
    and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, api):
        self.api = api

    def _list(self, url, response_key='results', obj_class=None,
              items=None, headers=None, params=None, limit=None,
              raw=False):

        if items is None:
            items = []
        if headers is None:
            headers = {}
        resp, body = self.api.get(url, headers=headers, params=params)

        if obj_class is None:
            obj_class = self.resource_class

        if response_key and response_key in body:
            data = body[response_key]
        else:
            data = body

        if raw or all([isinstance(res, str) for res in data]):
            new_items = data
        else:
            new_items = [obj_class(self, res, loaded=True)
                         for res in data if res]

        items = items + new_items
        if 'next' in body and body['next']:
            items = self._list(body['next'], response_key, obj_class, items,
                               headers, params, limit)

        return ListWithMeta(items, resp)

    def _delete(self, url, headers=None):
        if headers is None:
            headers = {}
        resp, body = self.api.delete(url, headers=headers)
        if body and body != '{}':
            return self.convert_into_with_meta(body, resp)
        return {}

    def _update(self, url, data, response_key=None, return_raw=False,
                headers=None):
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        data = json.dumps(data)
        resp, body = self.api.patch(url, data=data, headers=headers)
        if return_raw:
            if response_key:
                body = body[response_key]
            return self.convert_into_with_meta(body, resp)
        # PATCH requests may not return a body
        if body:
            if response_key:
                return self.resource_class(self, body[response_key], resp=resp,
                                           loaded=True)
            return self.resource_class(self, body, resp=resp, loaded=True)
        else:
            return StrWithMeta(body, resp)

    def _update_all(self, url, data, response_key=None, return_raw=False,
                    headers=None):
        if headers is None:
            headers = {}
        resp, body = self.api.put(url, data=data, headers=headers)
        if return_raw:
            if response_key:
                body = body[response_key]
            return self.convert_into_with_meta(body, resp)
        # PUT requests may not return a body
        if body:
            if response_key:
                return self.resource_class(self, body[response_key], resp=resp)
            return self.resource_class(self, body, resp=resp)
        else:
            return StrWithMeta(body, resp)

    def _create(self, url, data=None, response_key=None, return_raw=False,
                headers=None):
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        data = json.dumps(data)
        if data:
            resp, body = self.api.post(url, data=data, headers=headers)
        else:
            resp, body = self.api.post(url, headers=headers)
        if return_raw:
            if response_key:
                body = body[response_key]
            return self.convert_into_with_meta(body, resp)

        if response_key:
            return self.resource_class(self, body[response_key], resp=resp)
        return self.resource_class(self, body, resp=resp)

    def _get(self, url, response_key=None, return_raw=False, headers=None,
             params=None):
        if headers is None:
            headers = {}
        resp, body = self.api.get(url, headers=headers, params=params)
        if return_raw:
            if response_key:
                body = body[response_key]
            return self.convert_into_with_meta(body, resp)

        if response_key:
            return self.resource_class(self, body[response_key], loaded=True,
                                       resp=resp)
        return self.resource_class(self, body, loaded=True, resp=resp)

    def _post(self, url, data, response_key=None, return_raw=False,
              headers=None):
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        data = json.dumps(data)
        resp, body = self.api.post(url, data=data, headers=headers)
        if return_raw:
            if response_key:
                body = body[response_key]
            return self.convert_into_with_meta(body, resp)
        # POST requests may not return a body
        if body:
            if response_key:
                return self.resource_class(self, body[response_key], resp=resp,
                                           loaded=True)
            return self.resource_class(self, body, resp=resp, loaded=True)
        else:
            return StrWithMeta(body, resp)

    def _search(self, url, data, response_key='results', obj_class=None,
              items=None, headers=None, limit=None):

        if items is None:
            items = []
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        data = json.dumps(data)
        resp, body = self.api.post(url, headers=headers, data=data)

        if obj_class is None:
            obj_class = self.resource_class

        if response_key and response_key in body:
            data = body[response_key]
        else:
            data = body

        if all([isinstance(res, str) for res in data]):
            new_items = data
        else:
            new_items = [obj_class(self, res, loaded=True)
                         for res in data if res]

        items = items + new_items
        if 'next' in body and body['next']:
            items = self._list(body['next'], response_key, obj_class, items,
                               headers, None, limit)

        return ListWithMeta(items, resp)

    def convert_into_with_meta(self, item, resp):
        if isinstance(item, str):
            return StrWithMeta(item, resp)
        elif isinstance(item, bytes):
            return BytesWithMeta(item, resp)
        elif isinstance(item, list):
            return ListWithMeta(item, resp)
        elif isinstance(item, tuple):
            return TupleWithMeta(item, resp)
        elif item is None:
            return TupleWithMeta((), resp)
        else:
            return DictWithMeta(item, resp)


class ManagerWithFind(Manager, metaclass=abc.ABCMeta):
    """Manager with additional `find()`/`findall()` methods."""

    @abc.abstractmethod
    def list(self):
        pass

    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``.
        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        matches = self.findall(**kwargs)
        num = len(matches)

        if num == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(msg)
        elif num > 1:
            raise exceptions.NoUniqueMatch
        else:
            return self.get(matches[0].id)

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``.
        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        all_projects = kwargs.pop('all_projects', None)
        searches = kwargs.items()
        list_kwargs = {}
        if all_projects:
            list_kwargs = {'all_projects': True}
        for obj in self.list(**list_kwargs):
            try:
                if all(getattr(obj, attr) == value
                       for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue

        return found


class BasicManager(ManagerWithFind):

    def list(self, **kwargs):
        return self._list('/%s/' % self.base_url, params=kwargs)

    def get(self, resource_id):
        return self._get('/%s/%s/' % (self.base_url, resource_id))


class RequestIdMixin(object):
    """Wrapper class to expose x-openstack-request-id to the caller."""
    def request_ids_setup(self):
        self.x_openstack_request_ids = []

    @property
    def request_ids(self):
        return self.x_openstack_request_ids

    def append_request_ids(self, resp):
        """Add request_ids as an attribute to the object
        :param resp: Response object or list of Response objects
        """
        if isinstance(resp, list):
            # Add list of request_ids if response is of type list.
            for resp_obj in resp:
                self._append_request_id(resp_obj)
        elif resp is not None:
            # Add request_ids if response contains single object.
            self._append_request_id(resp)

    def _append_request_id(self, resp):
        if isinstance(resp, Response):
            # Extract 'X-Openstack-Request-Id' from headers if
            # response is a Response object.
            request_id = (resp.headers.get('Openstack-Request-Id')
                          or resp.headers.get('x-openstack-request-id')
                          or resp.headers.get('x-compute-request-id'))
        else:
            # If resp is of type string or None.
            request_id = resp
        if request_id not in self.x_openstack_request_ids:
            self.x_openstack_request_ids.append(request_id)


class Resource(RequestIdMixin):
    """Represents an instance of an object
    A resource represents a particular instance of an object (instance, type,
    etc). This is pretty much just a bag for attributes.
    :param manager: BaseManager object
    :param info: dictionary representing resource attributes
    :param loaded: prevent lazy-loading if set to True
    :param resp: Response or list of Response objects
    """

    DATE_FORMATS = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d']
    date_fields = []

    def __init__(self, manager, info, loaded=False, resp=None):
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._loaded = loaded
        self.request_ids_setup()
        self.append_request_ids(resp)

    def _add_details(self, info):
        for (k, v) in info.items():
            if k in self.date_fields and v is not None:
                parsed = False
                for dt_format in self.DATE_FORMATS:
                    try:
                        dt = datetime.strptime(v, dt_format)
                        if dt.tzinfo:
                            dt = dt.astimezone(LOCAL_TIMEZONE)
                        setattr(self, k, dt)
                        self._info[k] = dt
                        parsed = True
                        break
                    except Exception:
                        # Couldn't pasrse date, fallback to string
                        continue
                if parsed:
                    continue
                LOG.warning("Couldn't parse datetime for field %s", k)
            try:
                setattr(self, k, v)
                self._info[k] = v
            except AttributeError:
                # In this case we already defined the attribute
                # on the class
                pass

    def __setstate__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

    def __getattr__(self, k):
        if k not in self.__dict__:
            # NOTE(RuiChen): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)
            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_'
                          and k not in ('manager', 'x_openstack_request_ids'))
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def get(self):
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)
            # The 'request_ids' attribute has been added,
            # so store the request id to it instead of _info
            self.append_request_ids(new.request_ids)

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return NotImplemented
        # two resources of different types are not equal
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

    def __ne__(self, other):
        # Using not of '==' implementation because the not of
        # __eq__, when it returns NotImplemented, is returning False.
        return not self == other

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val

    def to_dict(self):
        return copy.deepcopy(self._info)


class ListWithMeta(list, RequestIdMixin):
    def __init__(self, values, resp):
        super(ListWithMeta, self).__init__(values)
        self.request_ids_setup()
        self.append_request_ids(resp)


class DictWithMeta(dict, RequestIdMixin):
    def __init__(self, values, resp):
        super(DictWithMeta, self).__init__(values)
        self.request_ids_setup()
        self.append_request_ids(resp)


class TupleWithMeta(tuple, RequestIdMixin):
    def __new__(cls, values, resp):
        return super(TupleWithMeta, cls).__new__(cls, values)

    def __init__(self, values, resp):
        self.request_ids_setup()
        self.append_request_ids(resp)


class StrWithMeta(str, RequestIdMixin):
    def __new__(cls, value, resp):
        return super(StrWithMeta, cls).__new__(cls, value)

    def __init__(self, values, resp):
        self.request_ids_setup()
        self.append_request_ids(resp)


class BytesWithMeta(bytes, RequestIdMixin):
    def __new__(cls, value, resp):
        return super(BytesWithMeta, cls).__new__(cls, value)

    def __init__(self, values, resp):
        self.request_ids_setup()
        self.append_request_ids(resp)
