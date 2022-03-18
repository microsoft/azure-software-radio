# pylint: disable=missing-function-docstring, missing-class-docstring
#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import os
import sys
import uuid
from gnuradio import gr
from azure.storage.blob import BlobServiceClient


def blob_setup(self):
    """ Pull a blob connection string from an environment variable.

    Use this to set up a separate blob service client for testing.
    """

    self.blob_connection_string = os.getenv(
        'AZURE_STORAGE_CONNECTION_STRING')
    if not self.blob_connection_string:
        print("Please set AZURE_STORAGE_CONNECTION_STRING env var to your storage account connection string")
        sys.exit()
    self.blob_service_client = BlobServiceClient.from_connection_string(
        self.blob_connection_string)

    # Create a unique name for the container
    self.test_blob_container_name = str(uuid.uuid4())
    self.container_client = self.blob_service_client.create_container(
        self.test_blob_container_name)

    self.tb = gr.top_block()


def blob_teardown(self):
    self.tb = None
    # clean up after test
    self.container_client.delete_container()
    self.blob_service_client.close()
