#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr_unittest
from azure_software_radio import keyvault
from azure_software_radio import default_credentials
import os

keyvault_name = os.getenv('AZURE_KEYVAULT_NAME')
key_name = os.getenv('AZURE_KEYVAULT_TEST_KEY')
key_val = "3.14"


class integration_keyvault(gr_unittest.TestCase):

    def test_no_default_cred(self):
        val = keyvault.pull_key(keyvault_name, key_name, '')
        self.assertTrue(val == key_val)

    def test_default_cred_provided(self):
        dc = default_credentials.get_default_creds(enable_cli_credential=True,
                                                   enable_environment=True,
                                                   enable_managed_identity=True,
                                                   enable_powershell=True,
                                                   enable_visual_studio_code=True,
                                                   enable_shared_token_cache=True,
                                                   enable_interactive_browser=False)
        val = keyvault.pull_key(keyvault_name, key_name, dc)
        self.assertTrue(val == key_val)


if __name__ == '__main__':
    gr_unittest.run(integration_keyvault)
