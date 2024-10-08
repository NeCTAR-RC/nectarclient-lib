# Copyright 2016 IBM Corp.
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

import requests

from nectarclient_lib import exceptions
from nectarclient_lib.tests.unit import utils


class ExceptionsTest(utils.TestCase):
    def test_from_response_no_body_message(self):
        # Tests that we get ClientException back since we don't have 500 mapped
        response = requests.Response()
        response.status_code = 500
        body = {'keys': ({})}
        ex = exceptions.from_response(response, body)
        self.assertIs(exceptions.ClientException, type(ex))
        self.assertEqual('Unknown Error', ex.message)
