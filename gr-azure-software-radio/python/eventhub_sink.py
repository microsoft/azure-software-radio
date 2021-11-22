#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr
from azure.eventhub import EventHubProducerClient, EventData
from azure.core.credentials import AzureSasCredential
from azure.identity import DefaultAzureCredential

import json
import numpy as np
import pmt


class EventHubSink(gr.sync_block):
    """ Converts GNU Radio PMT to JSON and sends event to Azure Event Hub.

    This block supports multiple ways to authenticate to Event Hub. Users can directly
    specify either a connection string, an SAS token, or use credentials
    supported by the DefaultAzureCredential class, such as environment variables.

        Args:
    Auth Method: Determines how to authenticate to Event Hub. May be one of
        "connection_string", "sas", or "default".
    Connection String: Event Hub connection string used for
        authentication if Auth Method is "connection_string".
    Shared Access Signature (SAS) token. This is required if using "default" or
        "sas" authentication.
    Event Hub Name: The Event Hub must be created in Azure before trying to
        send events to it.
    Event Hub Host Name:  The fully qualified host name for the Event Hub namespace. This is
        required if using "default" or "sas" authentication.
    """
    def __init__(self,authentication_method: str = "default", connection_str: str = None,
                sas_token: str = None, eventhub_name: str = None, eventhub_host_name: str = None):

        print('event sink init')
        gr.sync_block.__init__(self,
                        name="eventhub_sink",
                        in_sig=[],
                        out_sig=[])

        print('eventhub_sink start')
        self.eventhub_producer = get_eventhub_producer_client(
            authentication_method=authentication_method,
            eventhub_name=eventhub_name,
            connection_str=connection_str,
            sas_token=sas_token,
            eventhub_host_name=eventhub_host_name
        )

        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        print('eventhub_sink end')

    def handle_msg(self, msg):
        print('handling msg')
        pmsg = pmt.to_python(msg)
        print(pmsg)

        s = json.dumps(pmsg)
        self.eventhub_producer.send_batch(EventData(s))

    def work(self, input_items, output_items):
        return 0

    def stop(self):
        self.eventhub_producer.close()
        return True

def get_eventhub_producer_client(authentication_method: str = "default",  eventhub_name: str = None, connection_str: str = None,
                            sas_token: str = None, eventhub_host_name: str = None):
    """ Initialize the Event Hub Producer client

    Args:
        authentication_method (str): Determines which method to use to authenticate to Eventhub.
         May be one of "connection_string", "sas", or "default".
        eventhub_name (str): The path to the specified Event Hub to connect to.
        connection_str (optional, str): Eventhub connection string used for
            authentication if authentication_method is "connection_string"
        sas_token (optional, str): Shared Access Signature Token. This is required if using
            "sas" authentication.
        eventhub_host_name (optional, str): The fully qualified host name for the Event Hub namespace. This
            is required if using "sas" and "default" authentication.
    Raises:
        ValueError: Raised if an unsupported authentication method is used

    Returns:
        EventHubProducerClient: An Event Hub producer client ready to be used
    """
    if authentication_method == "connection_string":
        eventhub_producer_client = EventHubProducerClient.from_connection_string(connection_str,
                                                    eventhub_name=eventhub_name)

    elif authentication_method == "sas_token":
        credential = AzureSasCredential(sas_token)
        eventhub_producer_client = EventHubProducerClient(fully_qualified_namespace=eventhub_host_name,
                                                     eventhub_name=eventhub_name,
                                                     credential=credential)

    elif authentication_method == "default":
        default_credential = DefaultAzureCredential()
        eventhub_producer_client = EventHubProducerClient(fully_qualified_namespace=eventhub_host_name,
                                                     eventhub_name=eventhub_name,
                                                     credential=default_credential)
    else:
        raise ValueError("Unsupported authentication method specified")

    return eventhub_producer_client
