#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

import json
import pmt

from azure.eventhub import EventHubProducerClient, EventData
from azure.core.credentials import AzureSasCredential
from azure.identity import DefaultAzureCredential
from gnuradio import gr


# pylint: disable=abstract-method
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
    Event Hub Host Name:  The fully qualified host name for the Event Hub namespace. This is
        required if using "default" or "sas" authentication.
    Event Hub Name: The Event Hub must be created in Azure before trying to
        send events to it.
    Partition ID: The partition id to send events to.
    """
    # pylint: disable=too-many-arguments, no-member
    def __init__(
            self,
            authentication_method: str = "default",
            connection_str: str = None,
            sas_token: str = None,
            eventhub_host_name: str = None,
            eventhub_name: str = None,
            partition_id: str = None,
            default_credential=None):

        gr.sync_block.__init__(self,
                               name="eventhub_sink",
                               in_sig=[],
                               out_sig=[])

        if partition_id:
            self.partition_id = partition_id
        else:
            self.partition_id = None

        self.eventhub_producer = get_eventhub_producer_client(
            authentication_method=authentication_method,
            eventhub_name=eventhub_name,
            connection_str=connection_str,
            sas_token=sas_token,
            eventhub_host_name=eventhub_host_name,
            default_credential=default_credential
        )

        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)

    def handle_msg(self, msg):
        """
        This function handles the message passing operating (PMT message) from GNU Radio.
        It converts the PMT structure to python and later to JSON to send as an event.
        """
        pmsg = pmt.to_python(msg)
        jmsg = json.dumps(pmsg)
        event_batch = self.eventhub_producer.create_batch(
            partition_id=self.partition_id)
        event_batch.add(EventData(jmsg))
        self.eventhub_producer.send_batch(event_batch)

    def stop(self):
        self.eventhub_producer.close()
        return True


def get_eventhub_producer_client(
        authentication_method: str = "default",
        connection_str: str = None,
        sas_token: str = None,
        eventhub_host_name: str = None,
        eventhub_name: str = None,
        default_credential = None):
    """ Initialize the Event Hub Producer client

    Args:
        authentication_method (str): Determines which method to use to authenticate to Eventhub.
         May be one of "connection_string", "sas", or "default".
        connection_str (optional, str): Eventhub connection string used for
            authentication if authentication_method is "connection_string"
        sas_token (optional, str): Shared Access Signature Token. This is required if using
            "sas" authentication.
        eventhub_host_name (optional, str): The fully qualified host name for the Event Hub namespace. This
            is required if using "sas" and "default" authentication.
        eventhub_name (str): The path to the specified Event Hub to connect to.
        DefaultAzureCredential: The credential to use. Ignored if Auth Method is not "default" or not specified.
    Raises:
        ValueError: Raised if an unsupported authentication method is used

    Returns:
        EventHubProducerClient: An Event Hub producer client ready to be used
    """
    if authentication_method == "connection_string":
        eventhub_producer_client = EventHubProducerClient.from_connection_string(
            connection_str, eventhub_name=eventhub_name)

    elif authentication_method == "sas":
        credential = AzureSasCredential(sas_token)
        eventhub_producer_client = EventHubProducerClient(
            fully_qualified_namespace=eventhub_host_name,
            eventhub_name=eventhub_name,
            credential=credential)

    elif authentication_method == "default":
        if not default_credential:
            default_credential = DefaultAzureCredential()
        eventhub_producer_client = EventHubProducerClient(
            fully_qualified_namespace=eventhub_host_name,
            eventhub_name=eventhub_name,
            credential=default_credential)
    else:
        raise ValueError("Unsupported authentication method specified")

    return eventhub_producer_client
