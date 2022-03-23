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
import sys
import uuid
import json

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

        if not self.blob_connection_string:
            print(
                "Please set AZURE_STORAGE_CONNECTION_STRING env var to your storage account connection string")
            sys.exit()

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
    def test_repeat(self):
        """
        Test the repeat feature of blob source using a head block to limit the output length
        """
        blob_name = 'test-blob.npy'
        num_samples = 100000
        repeat_N_times = 3 # we limit the blob source when in repeat mode using a head block

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.float32)

        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        op_block = BlobSource(np_dtype=np.float32,
                              vlen=1,
                              authentication_method="connection_string",
                              connection_str=self.blob_connection_string,
                              container_name=self.test_blob_container_name,
                              blob_name=blob_name,
                              queue_size=4,
                              retry_total=0,
                              repeat=True) # Note we are repeating this time, the default is False

        vector_sink = blocks.vector_sink_f()
        head = blocks.head(4, num_samples*repeat_N_times)
        self.top_block.connect(op_block, head)
        self.top_block.connect(head, vector_sink)
        self.top_block.run()

        repeated_src_data = np.tile(src_data, repeat_N_times) # numpy tile will emulate what we're doing here
        self.assertEqual(repeated_src_data.tolist(), vector_sink.data())

    def test_sigmf(self):
        """
        Test the SigMF feature of blob source by looking at the stream tags on the first sample
        """
        blob_name = 'test-blob'
        num_samples = 100000

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.float32)

        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name + '.sigmf-data')
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        # Also upload a test meta file
        meta_blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name + '.sigmf-meta')
        meta_dict = {"global": {
                            "core:datatype": "cf32_le",
                            "core:sample_rate": 1000000.0,
                            "core:version": "1.0.0",
                            "core:hw": "test hardware info",
                            "core:author": "Marc",
                            "core:description": "test description"
                        },
                        "captures": [
                            {
                            "core:sample_start": 0,
                            "core:frequency": 2400000000.0
                            }
                        ],
                        "annotations": []
                    }
        meta_string = json.dumps(meta_dict, indent=2)
        meta_blob_client.upload_blob(data=meta_string, blob_type='BlockBlob')

        op_block = BlobSource(np_dtype=np.float32,
                              vlen=1,
                              authentication_method="connection_string",
                              connection_str=self.blob_connection_string,
                              container_name=self.test_blob_container_name,
                              blob_name=blob_name,
                              queue_size=4,
                              retry_total=0,
                              repeat=False,
                              sigmf=True) # Note we are enabling the SigMF feature
        vector_sink = blocks.vector_sink_f()
        tag_debug = blocks.tag_debug(gr.sizeof_float, '', "")
        tag_debug.set_display(True)
        self.top_block.connect(op_block, vector_sink)
        self.top_block.connect(op_block, tag_debug)
        self.top_block.run()

        self.assertEqual(src_data.tolist(), vector_sink.data())

        # There does not seem to be a way to retrieve the tags after the flowgraph finished
        #print(tag_debug.num_tags()) # Returning 0 for some reason, even though the tags definitely showed up
        #print(tag_debug.current_tags())

    def test_read_from_public_blob(self):
        """
        Upload data to public blob using the azure blob API and confirm we can read
        it back in without authenticating
        """
        url = os.getenv('AZURE_PUBLIC_STORAGE_URL')
        public_container_name = os.getenv('PUBLIC_CONTAINER_NAME')
        blob_name = 'test-blob.npy'
        num_samples = 1000000
        dtype = np.complex64
        sink = blocks.vector_sink_c()

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=dtype)
        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=public_container_name,
            blob=blob_name)
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        op_block = BlobSource(np_dtype=dtype,
                              vlen=1,
                              authentication_method="none",
                              url=url,
                              container_name=public_container_name,
                              blob_name=blob_name,
                              queue_size=4,
                              retry_total=0)

        self.top_block.connect(op_block, sink)
        self.top_block.run()

        self.assertEqual(src_data.tolist(), sink.data())


if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobSource)
