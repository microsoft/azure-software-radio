# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#


from gnuradio import gr_unittest
from gnuradio import blocks
from azure_software_radio import BlobSink
import azure_software_radio


class qa_BlobSink(gr_unittest.TestCase):

    # pylint: disable=invalid-name
    def setUp(self):
        self.blob_connection_string = (
            "DefaultEndpointsProtocol=https;AccountName=accountname;AccountKey=accountkey;"
            + "EndpointSuffix=core.windows.net"
        )

        self.tb = gr.top_block()

    # pylint: disable=invalid-name
    def tearDown(self):
        self.tb = None

    def test_instance(self):
        '''
        Ensure we don't throw errors in the constructor when given inputs with valid formats
        '''

        instance = BlobSink(authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name='test-instance',
                            block_len=500000,
                            queue_size=4)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertIsNotNone(instance)


if __name__ == '__main__':
    gr_unittest.run(qa_BlobSink)
