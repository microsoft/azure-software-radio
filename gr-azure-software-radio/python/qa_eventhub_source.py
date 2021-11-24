# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

import uuid
from gnuradio import gr, gr_unittest
from azure_software_radio import EventHubSource


class qa_EventHubSource(gr_unittest.TestCase):

    # pylint: disable=invalid-name
    def setUp(self):
        self.eventhub_consumer_connection_string = (
            "Endpoint=sb://<FQDN>/;SharedAccessKeyName=<KeyName>;SharedAccessKey=<KeyValue>"
        )

        self.tb = gr.top_block()
        self.test_consumer_eventhub_name = str(uuid.uuid4())

    # pylint: disable=invalid-name
    def tearDown(self):
        self.tb = None

    def test_instance(self):
        '''
        Ensure we don't throw errors in the constructor when given inputs with valid formats
        '''

        instance = EventHubSource(
            authentication_method="connection_string",
            connection_str=self.eventhub_consumer_connection_string,
            eventhub_name=self.test_consumer_eventhub_name,
            consumer_group="$Default",
            starting_position="@latest")

        self.assertIsNotNone(instance)


if __name__ == '__main__':
    gr_unittest.run(qa_EventHubSource)
