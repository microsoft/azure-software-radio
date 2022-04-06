# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member, eval-used, unused-variable, attribute-defined-outside-init
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

import ast
import time

from socket import socket
from fastapi import status
from gnuradio import gr_unittest

import httpx
from rest_api import RestApi


class QaRestApi(gr_unittest.TestCase):

    def get_free_port(self):
        with socket() as sock:
            sock.bind(('', 0))
            return sock.getsockname()[1]

    def test_instance(self):
        port = self.get_free_port()
        instance = RestApi(self, port)
        self.assertIsNotNone(instance)

    def test_get_status(self):
        self.check_var1 = 1
        self.check_var2 = '2'
        self.check_var3 = {'pi': 3.14}
        port = self.get_free_port()
        instance = RestApi(self, port, read_settings=['check_var1', 'check_var2', 'check_var3'])
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/status'
        resp = httpx.Client().get(addr_str)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dict_str = resp.content.decode("UTF-8")
        for i in range(1, 4):
            check_str = f'check_var{i}'
            self.assertEqual(check_str in dict_str, True)
        self.assertEqual('fake_var' in dict_str, False)

    def test_get_config(self):
        self.pi_val = 3.14
        self.pi_copy = self.pi_val
        port = self.get_free_port()
        instance = RestApi(self, port, write_settings=['pi_val'])
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/config'
        resp = httpx.Client().get(addr_str)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dict_str = resp.content.decode("UTF-8")
        res_dict = ast.literal_eval(dict_str)
        self.assertEqual(res_dict['pi_val'], self.pi_val)
        self.assertEqual('pi_copy' in dict_str, False)

    def test_put_config(self):
        self.pi_val = 0
        self.test_int = 1
        port = self.get_free_port()
        instance = RestApi(self, port, read_settings=['pi_val', 'test_int'], write_settings=['pi_val'])
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/config'
        resp = httpx.Client().put(addr_str, json={"pi_val": 3.14})
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dict_str = resp.content.decode("UTF-8")
        res_dict = ast.literal_eval(dict_str)
        self.assertEqual(res_dict['pi_val'], 3.14)

    def test_unauthorized_put_config(self):
        self.pi_val = 0
        port = self.get_free_port()
        instance = RestApi(self, port, read_settings=['pi_val'])
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/config'
        with httpx.Client() as client:
            resp = client.put(addr_str, json={"pi_val": 3.14})
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
            dict_str = resp.content.decode("UTF-8")
            self.assertEqual('pi_val' in dict_str, False)

    def test_bad_put_config(self):
        self.pi_val = 0
        port = self.get_free_port()
        instance = RestApi(self, port, read_settings=['pi_val'], write_settings=['pi_val'])
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/config'
        with httpx.Client() as client:
            resp = client.put(addr_str, json={"fake_val": 0})
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            dict_str = resp.content.decode("UTF-8")
            self.assertEqual('fake_val' in dict_str, False)


if __name__ == '__main__':
    gr_unittest.run(QaRestApi)
