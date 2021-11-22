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

from azure_software_radio import EventHubSink
from azure.eventhub import EventHubConsumerClient
from gnuradio import gr, gr_unittest
from gnuradio import blocks
from multiprocessing import Process

NUM_MSGS=10

class message_generator(gr.sync_block):
    def __init__(self, msg_list, msg_interval):
        gr.sync_block.__init__(
            self,
            name="message generator",
            in_sig=[np.float32],
            out_sig=None
        )
        self.msg_list = msg_list
        self.msg_interval = msg_interval
        self.msg_ctr = 0
        self.message_port_register_out(pmt.intern('out_port'))

    def work(self, input_items, output_items):
        inLen = len(input_items[0])
        while self.msg_ctr < len(self.msg_list) and \
                (self.msg_ctr * self.msg_interval) < \
                (self.nitems_read(0) + inLen):

            msg = pmt.make_dict()
            msg = pmt.dict_add(msg, pmt.string_to_symbol("this"), pmt.from_long(self.msg_ctr))
            msg = pmt.dict_add(msg, pmt.string_to_symbol("is"), pmt.from_long(self.msg_ctr))
            msg = pmt.dict_add(msg, pmt.string_to_symbol("a"), pmt.from_double(self.msg_ctr))
            msg = pmt.dict_add(msg, pmt.string_to_symbol("test"), pmt.from_long(self.msg_ctr))

            self.message_port_pub(pmt.intern('out_port'),
                                  msg)
            self.msg_ctr += 1
        return inLen

class IntegrationEventhubSink(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

        self.eventhub_connection_string = os.getenv('AZURE_EVENTHUB_CONNECTION_STRING')
        self.eventhub_consumer_group = os.getenv('AZURE_EVENTHUB_CONSUMER_GROUP')
        self.eventhub_name = os.getenv('AZURE_EVENTHUB_NAME')
        self.eventhub_consumer = EventHubConsumerClient.from_connection_string(
            conn_str=self.eventhub_connection_string,
            consumer_group=self.eventhub_consumer_group,
            eventhub_name=self.eventhub_name)
        self.num_rx_msgs = 0

    def tearDown(self):
        self.tb = None

    def on_event(self,partition_context,event):
        s = json.loads(list(event.body)[0])
        print('Received the event: %s'%s)
        self.num_rx_msgs += 1
        if self.num_rx_msgs == NUM_MSGS:
            self.eventhub_consumer.close()

    def test_round_trip_data_through_eventhub(self):
        test_start_time = datetime.datetime.utcnow()
        msg_interval = 1000
        msg_list = []
        for i in range(NUM_MSGS):
            msg_list.append(pmt.from_long(i))

        # Create dummy data to trigger messages
        src_data = []
        for i in range(NUM_MSGS * msg_interval):
            src_data.append(float(i))
        src = blocks.vector_source_f(src_data, False)
        pmt_msg_gen = message_generator(msg_list, msg_interval)

        sink_block = EventHubSink(authentication_method="connection_string",
                        connection_str=self.eventhub_connection_string,
                        eventhub_name=self.eventhub_name)

        # Connect vector source to message gen
        self.tb.connect(src, pmt_msg_gen)

        # Connect message generator to message consumer
        self.tb.msg_connect(pmt_msg_gen, 'out_port', sink_block, 'in')

        # Verify that the messgae port query functions work
        self.assertEqual(
            pmt.to_python(
                pmt_msg_gen.message_ports_out())[0],
            'out_port')
        self.assertEqual(
            'in' in pmt.to_python(
                sink_block.message_ports_in()), True)

        self.tb.run()
        with self.eventhub_consumer:
            self.eventhub_consumer.receive(on_event=self.on_event, starting_position=test_start_time)
        self.assertEqual(NUM_MSGS,self.num_rx_msgs)


if __name__ == '__main__':
    gr_unittest.run(IntegrationEventhubSink)
