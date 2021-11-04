#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np
import os
import uuid
from azure.storage.blob import BlobServiceClient
from azure_software_radio import blob_sink


class integration_blob_sink(gr_unittest.TestCase):

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

        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None
        # clean up after test
        self.container_client.delete_container()
        self.blob_service_client.close()

    

    def test_round_trip_data_through_blob(self):
        """ Upload known data to a blob using the blob_source block.

        Read this data back using the azure blob API and confirm that the data wasn't corrupted.
        """

        blob_name = 'test-blob.npy'
        block_len = 500000

        # set up a vector source with known complex data
        src_data = np.arange(0, 2*block_len, 1, dtype=np.complex64)
        src = blocks.vector_source_c(src_data)

        # set up a blob sink
        op = blob_sink(authentication_method="connection_string",
                       connection_str=self.blob_connection_string,
                       container_name=self.test_blob_container_name,
                       blob_name=blob_name,
                       block_len=block_len,
                       queue_size=4)

        self.tb.connect(src, op)
        # run the flowgraph
        self.tb.run()

        # connect to the test blob container and download the file
        # compare the file we downloaded against the samples in the vector source
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)

        result_data = np.frombuffer(blob_client.download_blob().readall(), dtype=np.complex64)

        # check data
        self.assertTrue((src_data == result_data).all())


if __name__ == '__main__':
    gr_unittest.run(integration_blob_sink)
