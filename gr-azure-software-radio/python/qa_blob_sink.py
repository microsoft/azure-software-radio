#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr, gr_unittest
import uuid
from azure_software_radio import blob_sink


class qa_blob_sink(gr_unittest.TestCase):

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

        instance = blob_sink(authentication_method="connection_string",
                             connection_str=self.blob_connection_string,
                             container_name=self.test_blob_container_name,
                             blob_name='test-instance',
                             block_len=500000,
                             queue_size=4)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertTrue(instance is not None)


if __name__ == '__main__':
    gr_unittest.run(qa_blob_sink)
