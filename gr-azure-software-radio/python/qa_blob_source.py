# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#


import uuid
from unittest.mock import patch

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np

from azure_software_radio import BlobSource


class qa_BlobSource(gr_unittest.TestCase):

    # pylint: disable=invalid-name
    def setUp(self):
        self.blob_connection_string = (
            "DefaultEndpointsProtocol=https;AccountName=accountname;AccountKey=accountkey;"
            + "EndpointSuffix=core.windows.net"
        )
        self.tb = gr.top_block()
        self.test_blob_container_name = str(uuid.uuid4())

    # pylint: disable=invalid-name
    def tearDown(self):
        self.tb = None

    def test_instance(self):
        '''
        Ensure we don't throw errors in the constructor when given inputs with valid formats
        '''

        instance = BlobSource(authentication_method="connection_string",
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

        op = BlobSource(authentication_method="connection_string",
                        connection_str=self.blob_connection_string,
                        container_name=self.test_blob_container_name,
                        blob_name=blob_name,
                        queue_size=4)

        src_data_bytes = src_data.tobytes()
        # don't send the last 2 bytes of the last sample
        chunk = src_data_bytes[:-2]
        data, chunk_residue = op.chunk_to_array(chunk=chunk, chunk_residue=b'')

        # check data - it should include all samples except the last one
        self.assertEqual(data.tolist(), src_data[:-1].tolist())
        # the chunk residue should be the first 6 bytes of the last sample
        self.assertEqual(chunk_residue, src_data_bytes[-8:-2])

    def test_chunk_residue_merge(self):
        '''
        Test that we can glue samples back together if we get them in separate chunks
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        op = BlobSource(authentication_method="connection_string",
                        connection_str=self.blob_connection_string,
                        container_name=self.test_blob_container_name,
                        blob_name=blob_name,
                        queue_size=4,
                        retry_total=0)

        src_data_bytes = src_data.tobytes()
        # don't send the first 2 bytes of the first sample
        chunk_residue_in = src_data_bytes[:2]
        chunk = src_data_bytes[2:]

        data, chunk_residue = op.chunk_to_array(chunk=chunk, chunk_residue=chunk_residue_in)

        # check data - it should include all samples with nothing left in the residue
        self.assertEqual(data.tolist(), src_data.tolist())
        self.assertEqual(len(chunk_residue), 0)

    @patch.object(BlobSource, 'blob_auth_and_container_info_is_valid', return_value=True)
    def test_end_to_end_run(self, _):
        '''
        Test the block properly starts up, reads data from the blob data queue, and cleanly
        shuts down
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        dst = blocks.vector_sink_c()

        # prevent setup_blob_iterator from making Azure API calls
        with patch.object(BlobSource, 'setup_blob_iterator', spec=iter) as mock_iter:
            # add in a list of chunks we want to pretend the blob API gave us
            mock_iter.return_value = iter([src_data.tobytes()])

            op = BlobSource(authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            queue_size=4,
                            retry_total=0)

            self.tb.connect(op, dst)

            self.tb.run()

        self.assertEqual(dst.data(), src_data.tolist())

if __name__ == '__main__':
    gr_unittest.run(qa_BlobSource)
