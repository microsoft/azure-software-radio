#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from azure_software_radio import blob_source
import numpy as np
import uuid

from unittest.mock import patch

class qa_blob_source(gr_unittest.TestCase):

    def setUp(self):
        self.blob_connection_string = ( 
            "DefaultEndpointsProtocol=https;AccountName=accountname;AccountKey=accountkey;"
            + "EndpointSuffix=core.windows.net"
        )

        # Create a unique name for the container
        self.test_blob_container_name = str(uuid.uuid4())
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None


    def test_instance(self):
        '''
        Ensure we don't throw errors in the constructor when given inputs with valid formats
        '''

        instance = blob_source(authentication_method="connection_string",
                               connection_str=self.blob_connection_string,
                               container_name=self.test_blob_container_name,
                               blob_name='test-instance',
                               queue_size=4)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertIsNotNone(instance)


    def test_chunk_residue(self):
        '''
        Test that we don't crash if we get back a non-integer number of samples from a blob chunk
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        op = blob_source(authentication_method="connection_string",
                         connection_str=self.blob_connection_string,
                         container_name=self.test_blob_container_name,
                         blob_name=blob_name,
                         queue_size=4)

        src_data_bytes = src_data.tobytes()
        # don't send the last 2 bytes of the last sample
        chunk = src_data_bytes[:-2]
        data, chunk_residue = op.chunk_to_array(chunk=chunk, chunk_residue=b'')

        # check data - it should include all samples except the last one
        self.assertTrue((data == src_data[:-1]).all())
        # the chunk residue should be the first 6 bytes of the last sample
        self.assertTrue((chunk_residue == src_data_bytes[-8:-2]))


    def test_chunk_residue_merge(self):
        '''
        Test that we can glue samples back together if we get them in separate chunks
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        op = blob_source(authentication_method="connection_string",
                         connection_str=self.blob_connection_string,
                         container_name=self.test_blob_container_name,
                         blob_name=blob_name,
                         queue_size=4)

        src_data_bytes = src_data.tobytes()
        # don't send the first 2 bytes of the first sample
        chunk_residue_in = src_data_bytes[:2]
        chunk = src_data_bytes[2:]

        data, chunk_residue = op.chunk_to_array(chunk=chunk, chunk_residue=chunk_residue_in)

        # check data - it should include all samples with nothing left in the residue
        self.assertTrue((data == src_data).all())
        self.assertEquals(len(chunk_residue), 0)

    def test_end_to_end_run(self):
        '''
        Test the block properly starts up, reads data from the blob data queue, and cleanly
        shuts down
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        dst = blocks.vector_sink_c()

        # prevent setup_blob_iterator from making Azure API calls
        with patch.object(blob_source, 'setup_blob_iterator', spec=iter) as mock_iter:
            # add in a list of chunks we want to pretend the blob API gave us
            mock_iter.return_value = iter([src_data.tobytes()])
            
            op = blob_source(authentication_method="connection_string",
                             connection_str=self.blob_connection_string,
                             container_name=self.test_blob_container_name,
                             blob_name=blob_name,
                             queue_size=4)

            self.tb.connect(op, dst)

            self.tb.run()
        
        self.assertTrue((dst.data() == src_data).all())

if __name__ == '__main__':
    gr_unittest.run(qa_blob_source)
