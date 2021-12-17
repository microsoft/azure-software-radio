# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
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
import json
import os
import time
import pmt

from azure_software_radio import EventHubSource, default_credentials
from azure.eventhub import EventHubProducerClient, EventData
from gnuradio import blocks
from gnuradio import gr, gr_unittest

class IntegrationEventhubSource(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

        self.eventhub_connection_string = os.getenv(
            'AZURE_EVENTHUB_CONNECTION_STRING')
        self.eventhub_consumer_group = os.getenv(
            'AZURE_EVENTHUB_CONSUMER_GROUP')
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
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("this"),
            pmt.from_long(0))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("is"), pmt.from_long(1))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("a"),
            pmt.from_double(2))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("test"),
            pmt.from_long(3))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("for"),
            pmt.from_double(4))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("eventhub source"),
            pmt.from_long(5))

        msg = json.dumps(pmt.to_python(pmsg))
        event_batch = self.eventhub_producer.create_batch()
        event_batch.add(EventData(msg))
        self.eventhub_producer.send_batch(event_batch)

        msg_debug_block = blocks.message_debug()

        source_block = EventHubSource(
            authentication_method="connection_string",
            connection_str=self.eventhub_connection_string,
            eventhub_name=self.eventhub_name,
            consumer_group=self.eventhub_consumer_group,
            starting_position=test_start_time)

        self.tb.msg_connect(source_block, 'out', msg_debug_block, 'print')
        self.tb.msg_connect(source_block, 'out', msg_debug_block, 'store')

        self.assertEqual(
            pmt.to_python(
                source_block.message_ports_out())[0],
            'out')
        self.assertEqual(
            msg_debug_block.num_messages(), 0)

        self.tb.start()
        time.sleep(1)
        self.assertEqual(
            msg_debug_block.num_messages(), 1)
        source_block.stop()
        self.tb.stop()
        self.tb.wait()

    def test_round_trip_data_through_eventhub_default_cred(self):

        creds = default_credentials.get_DefaultAzureCredential(enable_cli_credential=True,
                                                               enable_environment=True,
                                                               enable_managed_identity=True,
                                                               enable_powershell=True,
                                                               enable_visual_studio_code=True,
                                                               enable_shared_token_cache=True,
                                                               enable_interactive_browser=False)

        test_start_time = datetime.datetime.utcnow()

        pmsg = pmt.make_dict()
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("this"),
            pmt.from_long(0))
        pmsg = pmt.dict_add(pmsg, pmt.string_to_symbol("is"), pmt.from_long(1))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("a"),
            pmt.from_double(2))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("test"),
            pmt.from_long(3))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("for"),
            pmt.from_double(4))
        pmsg = pmt.dict_add(
            pmsg,
            pmt.string_to_symbol("eventhub"),
            pmt.from_long(5))

        msg = json.dumps(pmt.to_python(pmsg))
        event_batch = self.eventhub_producer.create_batch()
        event_batch.add(EventData(msg))
        self.eventhub_producer.send_batch(event_batch)

        msg_debug_block = blocks.message_debug()

        source_block = EventHubSource(
            authentication_method="default",
            connection_str=self.eventhub_connection_string,
            eventhub_name=self.eventhub_name,
            consumer_group=self.eventhub_consumer_group,
            starting_position=test_start_time,
            default_credential=creds)

        self.tb.msg_connect(source_block, 'out', msg_debug_block, 'print')
        self.tb.msg_connect(source_block, 'out', msg_debug_block, 'store')

        self.assertEqual(
            pmt.to_python(
                source_block.message_ports_out())[0],
            'out')
        self.assertEqual(
            msg_debug_block.num_messages(), 0)

        self.tb.start()
        time.sleep(1)
        self.assertEqual(
            msg_debug_block.num_messages(), 1)
        source_block.stop()
        self.tb.stop()
        self.tb.wait()



if __name__ == '__main__':
    gr_unittest.run(IntegrationEventhubSource)
