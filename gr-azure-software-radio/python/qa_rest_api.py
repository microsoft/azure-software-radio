#!/usr/bin/env python

from gnuradio import gr, gr_unittest
# from gnuradio import blocks
from rest_api import RestApi
import requests
import time
from socket import socket


class qa_rest_api(gr_unittest.TestCase):
    '''
    def __init__(self):
        self.check_var1 = None
        self.check_var2 = None
        self.check_var3 = None
        self.pi = None
        self.val = None
    '''
    def get_free_port(self):
        with socket() as s:
            s.bind(('', 0))
            return s.getsockname()[1]

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
        r = requests.get(addr_str)
        for i in range(1, 4):
            check_str = f'check_var{i}'
            self.assertEqual(check_str in r.text, True)
        self.assertEqual('fake_var' in r.text, False)

    def test_get_by_name(self):
        self.pi = 3.14
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        p = "name=pi"
        addr_str = 'http://127.0.0.1:' + str(port) + '/get-by-name'
        r = requests.get(addr_str, params=p)
        res = eval(r.text)
        self.assertEqual(res['pi'], 3.14)
    
    def test_set_by_name(self):
        self.pi = 0
        port = self.get_free_port()
        instance = RestApi(self, port)
        # give server a second to startup
        time.sleep(1)
        addr_str = 'http://127.0.0.1:' + str(port) + '/set-by-name'
        r = requests.put(addr_str, json={"pi": 3.14})
        #print(r.text)
        res = eval(r.text)
        self.assertEqual(self.pi, 3.14)
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
        r = requests.put(addr_str, json={"set_var": 99})
        res = eval(r.text)
        self.assertEqual(self.val, 99)
        self.assertEqual(res['Ran'], 'ok')

if __name__ == '__main__':
    gr_unittest.run(qa_rest_api)
