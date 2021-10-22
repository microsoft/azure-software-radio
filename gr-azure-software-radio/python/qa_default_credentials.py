#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr, gr_unittest
import pytest
# from gnuradio import blocks
from default_credentials import default_credentials

class qa_default_credentials(gr_unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_instance(self):

        instance = default_credentials.get_default_creds(enable_cli_credential=True,
                                       enable_environment=True,
                                       enable_managed_identity=True,
                                       enable_powershell=True,
                                       enable_visual_studio_code=True,
                                       enable_shared_token_cache=True,
                                       enable_interactive_browser=False)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertTrue(instance is not None)

    def test_001_environment_only(self):
        instance = default_credentials.get_default_creds(enable_cli_credential=False,
                                       enable_environment=True,
                                       enable_managed_identity=False,
                                       enable_powershell=False,
                                       enable_visual_studio_code=False,
                                       enable_shared_token_cache=True,
                                       enable_interactive_browser=False)

        if len(instance.credentials)!=1:
            print("Environment var auth failed, unexpected number of credentials.")
            pytest.fail()
        if 'EnvironmentCredential' not in str(instance.credentials[0]):
            print("Environment var auth failed, first credential is not environment.")
            pytest.fail()

    def test_002_managed_identity_only(self):
        instance = default_credentials.get_default_cred(enable_cli_credential=False,
                                       enable_environment=False,
                                       enable_managed_identity=True,
                                       enable_powershell=False,
                                       enable_visual_studio_code=False,
                                       enable_shared_token_cache=True,
                                       enable_interactive_browser=False)

        if len(instance.credentials)!=1:
            print("Managed Identity auth failed, unexpected number of credentials.")
            pytest.fail()
        if 'ManagedIdentityCredential' not in str(instance.credentials[0]):
            print("Managed Identity auth failed, first credential is not managed identity.")
            pytest.fail()
            
    
if __name__ == '__main__':
    gr_unittest.run(qa_default_credentials)
