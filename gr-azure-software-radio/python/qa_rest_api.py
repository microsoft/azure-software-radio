# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member, eval-used, unused-variable
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr, gr_unittest
from rest_api import RestApi
import requests
import time
from socket import socket


class QaRestApi(gr_unittest.TestCase):

    def get_free_port(self):
        with socket() as sock:
            sock.bind(('', 0))
            return sock.getsockname()[1]

    def test_instance(self):
        port = self.get_free_port()
        instance = RestApi(self, port)
        self.assertIsNotNone(instance)

    def test_get_vars(self):
        self.check_var1 = 1
        self.check_var2 = '2'
        self.check_var3 = {'pi':3.14}
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/get-locals'
        resp = requests.get(addr_str)
        for i in range(1, 4):
            check_str = f'check_var{i}'
            self.assertEqual(check_str in resp.text, True)
        self.assertEqual('fake_var' in resp.text, False)

    def test_get_by_name(self):
        self.pi_val = 3.14
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        para = "name=pi_val"
        addr_str = 'http://127.0.0.1:' + str(port) + '/get-by-name'
        resp = requests.get(addr_str, params=para)
        res = eval(resp.text)
        self.assertEqual(res['pi_val'], 3.14)

    def test_set_by_name(self):
        self.pi_val = 0
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/set-by-name'
        resp = requests.put(addr_str, json={"pi_val": 3.14})
        #print(r.text)
        res = eval(resp.text)
        self.assertEqual(self.pi_val, 3.14)
        self.assertEqual(res['All'], 'set')

    def set_var(self, val):
        self.val = val

    def test_call_by_name(self):
        self.val = None
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/call-by-name'
        resp = requests.put(addr_str, json={"set_var": 99})
        res = eval(resp.text)
        self.assertEqual(self.val, 99)
        self.assertEqual(res['Ran'], 'ok')

if __name__ == '__main__':
    gr_unittest.run(QaRestApi)
