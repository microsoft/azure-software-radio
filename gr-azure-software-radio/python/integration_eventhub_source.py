#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

"""
Integration tests for functions from eventhub_sink.py
"""

import datetime
import numpy as np
import json
import os
import pmt
import time

from azure_software_radio import EventHubSource
from azure.eventhub import EventHubProducerClient, EventData
from gnuradio import gr, gr_unittest
from gnuradio import blocks

class pmt_message_consumer(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="pmt message consumer",
            in_sig=[],
            out_sig=[]
        )
        self.msg_list = []
        self.message_port_register_in(pmt.intern('in_port'))
        self.set_msg_handler(pmt.intern('in_port'),
                             self.handle_msg)

    def handle_msg(self, msg):
        self.msg_list.append(msg)
        print('Received PMT message %s'%msg)

class IntegrationEventhubSource(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

        self.eventhub_connection_string = os.getenv('AZURE_EVENTHUB_CONNECTION_STRING')
        self.eventhub_consumer_group = os.getenv('AZURE_EVENTHUB_CONSUMER_GROUP')
        self.eventhub_name = os.getenv('AZURE_EVENTHUB_NAME')
        self.eventhub_producer = EventHubProducerClient.from_connection_string(
            conn_str=self.eventhub_connection_string,
            eventhub_name=self.eventhub_name)

    def tearDown(self):
        self.tb = None
        self.eventhub_producer.close()

    def test_round_trip_data_through_eventhub(self):
        test_start_time = datetime.datetime.utcnow()

        pmsg = pmt.make_dict()
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("this"), pmt.from_long(0))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("is"), pmt.from_long(1))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("a"), pmt.from_double(2))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("test"), pmt.from_long(3))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("for"), pmt.from_double(4))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("eventhub"), pmt.from_long(5))

        msg = json.dumps(pmt.to_python(pmsg))
        event_batch = self.eventhub_producer.create_batch()
        event_batch.add(EventData(msg))
        self.eventhub_producer.send_batch(event_batch)

        pmt_msg_rec = pmt_message_consumer() 

        source_block = EventHubSource(authentication_method="connection_string",
                        connection_str=self.eventhub_connection_string,
                        eventhub_name=self.eventhub_name,
                        consumer_group=self.eventhub_consumer_group,
                        starting_position=test_start_time)

        self.tb.msg_connect(source_block, 'out', pmt_msg_rec, 'in_port')

        self.assertEqual(
            pmt.to_python(
                source_block.message_ports_out())[0],
            'out')
        self.assertEqual(
            'in_port' in pmt.to_python(
                pmt_msg_rec.message_ports_in()), True)

        self.tb.run()
        print('after run')
        self.assertEqual(len(pmt_msg_rec.msg_list), 1)



if __name__ == '__main__':
    gr_unittest.run(IntegrationEventhubSource)
