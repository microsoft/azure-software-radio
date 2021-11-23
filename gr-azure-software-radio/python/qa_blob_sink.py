# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from unittest.mock import DEFAULT, patch
import uuid

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import numpy as np

import azure_software_radio.blob_sink
from azure_software_radio import BlobSink


class qa_BlobSink(gr_unittest.TestCase):

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

        instance = BlobSink(np_dtype=np.complex64,
                            vlen=1,
                            authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name='test-instance',
                            block_len=500000,
                            queue_size=4)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertIsNotNone(instance)

    @patch.object(azure_software_radio.blob_sink, "blob_container_info_is_valid")
    @patch.multiple(BlobSink,
                    create_blob=DEFAULT,
                    stage_block=DEFAULT,
                    stop=DEFAULT)
    def test_end_to_end_run(self, _, create_blob, stage_block, stop): # pylint: disable=unused-argument
        '''
        Test the block properly starts up, reads data from the blob data queue, and cleanly
        shuts down
        '''

        stop.return_value = True

        blob_name = 'test-blob.npy'
        num_samples = 50000
        block_len = 25000

        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        src = blocks.vector_source_c(src_data)

        op_block = BlobSink(np_dtype=np.complex64,
                            vlen=1,
                            authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            block_len=block_len,
                            queue_size=4,
                            retry_total=0)

        self.tb.connect(src, op_block)

        self.tb.run()

        # confirm that our code called the "stage_block" function the expected number of times
        # with the expected inputs
        expected_uploads = [src_data[:block_len].view(np.byte).tolist(),
                            src_data[block_len:].view(np.byte).tolist()]
        # call_args_list is a list of call objects. Each call object acts like a tuple, with the first
        # element of the tuple containing positional arguments. The positional arguments themselves are a tuple of all
        # the arguments passed in, so we have a list of tuples of tuples.
        result_uploads = [c[0][0].tolist() for c in stage_block.call_args_list]
        self.assertListEqual(expected_uploads, result_uploads)


if __name__ == '__main__':
    gr_unittest.run(qa_BlobSink)
