#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
# pylint: disable=invalid-name

"""
Integration tests for functions from blob_source.py
"""

import os
import uuid

import azure.core.exceptions as az_exceptions
from azure.storage.blob import BlobServiceClient

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np

from azure_software_radio import BlobSource


class IntegrationBlobSource(gr_unittest.TestCase):
    """ Test case class for running integration tests on blob_source.py
    """

    # pylint: disable=invalid-name
    def setUp(self):
        """ Pull a blob connection string from an environment variable.

        Use this to set up a separate blob service client for testing.
        """
        self.blob_connection_string = os.getenv(
            'AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.blob_connection_string)
        # Create a unique name for the container
        self.test_blob_container_name = str(uuid.uuid4())
        self.container_client = self.blob_service_client.create_container(
            self.test_blob_container_name)
        self.top_block = gr.top_block()

    # pylint: disable=invalid-name
    def tearDown(self):
        '''
        Teardown all resources
        '''
        self.top_block = None

        # clean up after test
        self.container_client.delete_container()
        self.blob_service_client.close()

    def test_round_trip_data_through_blob(self):
        """ Upload known data to a blob using the azure blob API.

        Read this data back into a GNU Radio vector sink using the blob_source
        block and confirm that the data wasn't corrupted.
        """

        blob_name = 'test-blob.npy'
        num_samples = 1000000

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)
        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        op_block = BlobSource(authentication_method="connection_string",
                              connection_str=self.blob_connection_string,
                              container_name=self.test_blob_container_name,
                              blob_name=blob_name,
                              queue_size=4)
        dst = blocks.vector_sink_c()

        self.top_block.connect(op_block, dst)
        self.top_block.run()

        self.assertEqual(src_data.tolist(), dst.data())

    def test_read_from_nonexistent_blob(self):
        """
        Confirm we get the failure we expect when trying to read from a blob that doesn't exist
        """

        blob_name = 'test-blob.npy'

        op_block = BlobSource(authentication_method="connection_string",
                              connection_str=self.blob_connection_string,
                              container_name=self.test_blob_container_name,
                              blob_name=blob_name,
                              queue_size=4,
                              retry_total=0)
        src_data = [[]]
        output_items = [[]]

        with self.assertRaises(az_exceptions.ResourceNotFoundError):
            # calling work directly, since exceptions raised by a block when run with top_block.run() get
            # passed through the GNU Radio runtime and aren't directly accessible
            op_block.work(src_data, output_items)


if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobSource)
