#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.

"""
Integration tests for functions from blob_sink.py
"""

import os
import uuid

import azure.core.exceptions as az_exceptions
from azure.storage.blob import BlobServiceClient
from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np
import urllib3.exceptions

from azure_software_radio import BlobSink


class IntegrationBlobSink(gr_unittest.TestCase):
    """ Test case class for running integration tests on blob_sink.py
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
        """ Clean up after test
        """
        self.top_block = None
        self.container_client.delete_container()
        self.container_client.close()
        self.blob_service_client.close()

    def round_trip_test_helper(self, dtype, src, vlen=1):
        """ Helper script for running round trip tests against a variety of data types

        Note: The vlen used must evenly divide into block_len

        Args:
            dtype (np datatype object): what datatype to use for the source data array
            item_size (int): what is the itemsize for the block, including vector length
            sink (gnuradio vector sink block): vector sink type appropriate for the dtype
        """
        blob_name = 'test-blob.npy'
        block_len = 500000

        src_data = np.arange(0, 2*block_len, 1, dtype=dtype)
        src.set_data(src_data.tolist())

        op_block = BlobSink(np_dtype=dtype,
                            vlen=vlen,
                            authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            block_len=block_len,
                            queue_size=4,
                            retry_total=0)

        self.top_block.connect(src, op_block)
        self.top_block.run()

        # connect to the test blob container and download the file
        # compare the file we downloaded against the samples in the vector source
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)

        result_data = np.frombuffer(blob_client.download_blob().readall(), dtype=dtype)
        self.assertEqual(src_data.tolist(), result_data.tolist())

    def test_round_trip_complex_float_data_through_blob(self):
        """
        Upload known np.complex64 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.complex64,
                                    src=blocks.vector_source_c([]))

    def test_round_trip_float_data_through_blob(self):
        """
        Upload known np.float32 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.float32,
                                    src=blocks.vector_source_f([]))

    def test_round_trip_int32_data_through_blob(self):
        """
        Upload known np.int32 data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.int32,
                                    src=blocks.vector_source_i([]))

    def test_round_trip_char_data_through_blob(self):
        """
        Upload known np.byte data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """

        self.round_trip_test_helper(dtype=np.ubyte,
                                    src=blocks.vector_source_b([]))

    def test_round_trip_complex_float_vector_data_through_blob(self):
        """
        Upload known np.complex64 vector data to a blob using the azure blob API and
        confirm it doesn't get corrupted
        """
        vlen = 10
        self.round_trip_test_helper(dtype=np.complex64,
                                    src=blocks.vector_source_c([], vlen=vlen),
                                    vlen=vlen)

    def test_write_to_read_only_container(self):
        """
        Confirm we get the failure we expect when trying to write a blob to a container where we do not have
        write access
        """

        url = os.getenv('AZURE_STORAGE_URL')
        read_only_sas = os.getenv('AZURE_STORAGE_READONLY_SAS')

        blob_name = 'test-blob.npy'
        block_len = 500

        op_block = BlobSink(np_dtype=np.complex64,
                            vlen=1,
                            authentication_method="url_with_sas",
                            url=url + '/' + read_only_sas,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            block_len=block_len,
                            queue_size=4,
                            retry_total=0)

        with self.assertRaises(az_exceptions.HttpResponseError):
            op_block.create_blob()

    def test_write_to_malformed_container_url(self):
        """
        Confirm we fail in create_blob if trying to use a malformed URL, such as
        using a URL ending in a slash when using url_with_sas authentication
        """

        url = os.getenv('AZURE_STORAGE_URL')
        read_only_sas = os.getenv('AZURE_STORAGE_READONLY_SAS')

        # trigger a failure by including multiple slashes in the URL
        bad_url = url + '//' + read_only_sas

        blob_name = 'test-blob.npy'
        block_len = 500

        op_block = BlobSink(np_dtype=np.complex64,
                            vlen=1,
                            authentication_method="url_with_sas",
                            url=bad_url,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            block_len=block_len,
                            queue_size=4,
                            retry_total=0)

        with self.assertRaises(urllib3.exceptions.LocationParseError):
            op_block.create_blob()



if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobSink)
