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
        self.blob_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.blob_connection_string)
        # Create a unique name for the container
        self.test_blob_container_name = str(uuid.uuid4())
        self.container_client = self.blob_service_client.create_container(
            self.test_blob_container_name)
        self.top_block = gr.top_block(catch_exceptions=False)

    # pylint: disable=invalid-name
    def tearDown(self):
        '''
        Teardown all resources
        '''
        self.top_block = None

        # clean up after test
        self.container_client.delete_container()
        self.container_client.close()
        self.blob_service_client.close()

    def test_read_from_nonexistent_blob(self):
        """
        Confirm we get the failure we expect when trying to read from a blob that doesn't exist
        """

        blob_name = 'test-blob.npy'

        op_block = BlobSource(np_dtype=np.complex64,
                              vlen=1,
                              authentication_method="connection_string",
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

    def round_trip_test_helper(self, dtype, sink, vlen=1):
        """ Helper script for running round trip tests against a variety of data types

        Args:
            dtype (np datatype object): what datatype to use for the source data array
            item_size (int): what is the itemsize for the block, including vector length
            sink (gnuradio vector sink block): vector sink type appropriate for the dtype
        """
        blob_name = 'test-blob.npy'
        num_samples = 1000000

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=dtype)
        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        op_block = BlobSource(np_dtype=dtype,
                              vlen=vlen,
                              authentication_method="connection_string",
                              connection_str=self.blob_connection_string,
                              container_name=self.test_blob_container_name,
                              blob_name=blob_name,
                              queue_size=4,
                              retry_total=0)

        self.top_block.connect(op_block, sink)
        self.top_block.run()

        self.assertEqual(src_data.tolist(), sink.data())

    def test_round_trip_complex_float_data_through_blob(self):
        """
        Upload known np.complex64 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.complex64,
                                    sink=blocks.vector_sink_c())

    def test_round_trip_float_data_through_blob(self):
        """
        Upload known np.float32 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.float32,
                                    sink=blocks.vector_sink_f())

    def test_round_trip_int32_data_through_blob(self):
        """
        Upload known np.int32 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.int32,
                                    sink=blocks.vector_sink_i())

    def test_round_trip_char_data_through_blob(self):
        """
        Upload known np.byte data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.ubyte,
                                    sink=blocks.vector_sink_b())

    def test_round_trip_complex_float_vector_data_through_blob(self):
        """
        Upload known np.complex64 vector data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """
        vlen = 10
        self.round_trip_test_helper(dtype=np.complex64,
                                    sink=blocks.vector_sink_c(vlen=vlen),
                                    vlen=vlen)

if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobSource)
