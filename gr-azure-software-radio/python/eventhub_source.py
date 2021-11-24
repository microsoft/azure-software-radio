#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

import json
import threading
import pmt

from gnuradio import gr
from azure.eventhub import EventHubConsumerClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureSasCredential

# pylint: disable=abstract-method
class EventHubSource(gr.sync_block):
    """ Receives and converts JSON events from Azure Event Hub to GNU Radio PMT format.

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
        receive events from.
    Consumer Group: The consumer group to receive events from Event Hub.
    Partition ID: The partition ID to receive events from.
    Starting Position: The position of an event in the Event Hub partition.
    """
    # pylint:  disable=too-many-arguments, no-member
    def __init__(
            self,
            authentication_method: str = "default",
            connection_str: str = None,
            sas_token: str = None,
            eventhub_host_name: str = None,
            eventhub_name: str = None,
            consumer_group: str = None,
            partition_id: str = None,
            starting_position=None):

        gr.sync_block.__init__(self,
                               name="eventhub_source",
                               in_sig=[],
                               out_sig=[])

        self.starting_position = starting_position
        if partition_id:
            self.partition_id = partition_id
        else:
            self.partition_id = None

        self.eventhub_consumer = get_eventhub_consumer_client(
            authentication_method=authentication_method,
            connection_str=connection_str,
            sas_token=sas_token,
            eventhub_host_name=eventhub_host_name,
            eventhub_name=eventhub_name,
            consumer_group=consumer_group,
        )

        self.message_port_register_out(pmt.intern('out'))

        self.rec_thread = threading.Thread(target=self.receive)
        self.rec_thread.start()

    def receive(self):
        """
        Receive events from event hub given the specified partition and starting position.
        The receive call is blocking and must be run in a dedicated thread.
        """
        self.eventhub_consumer.receive(
            on_event=self.on_event,
            partition_id=self.partition_id,
            starting_position=self.starting_position)

    def on_event(self, _partition_context, event):
        """
        Convert the received JSON message to PMT. The expected Event Hub event only has one message batched.
        """
        # pylint: disable=no-member
        msg = json.loads(list(event.body)[0])
        pmsg = pmt.to_pmt(msg)
        self.message_port_pub(pmt.intern("out"), pmsg)

    def stop(self):
        self.eventhub_consumer.close()
        self.rec_thread.join()
        return True


def get_eventhub_consumer_client(
        authentication_method: str = "default",
        connection_str: str = None,
        sas_token: str = None,
        eventhub_host_name: str = None,
        eventhub_name: str = None,
        consumer_group: str = None):
    """ Initialize the Event Hub Consumer client

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
        consumer_group (str): The consumer group to receive events from Event Hub.
    Raises:
        ValueError: Raised if an unsupported authentication method is used

    Returns:
        EventHubConsumerClient: An Event Hub consumer client ready to be used
    """
    if authentication_method == "connection_string":
        eventhub_consumer_client = EventHubConsumerClient.from_connection_string(
            connection_str, eventhub_name=eventhub_name, consumer_group=consumer_group)

    elif authentication_method == "sas_token":
        credential = AzureSasCredential(sas_token)
        eventhub_consumer_client = EventHubConsumerClient(
            fully_qualified_namespace=eventhub_host_name,
            eventhub_name=eventhub_name,
            consumer_group=consumer_group,
            credential=credential)

    elif authentication_method == "default":
        default_credential = DefaultAzureCredential()
        eventhub_consumer_client = EventHubConsumerClient(
            fully_qualified_namespace=eventhub_host_name,
            eventhub_name=eventhub_name,
            consumer_group=consumer_group,
            credential=default_credential)
    else:
        raise ValueError("Unsupported authentication method specified")

    return eventhub_consumer_client
