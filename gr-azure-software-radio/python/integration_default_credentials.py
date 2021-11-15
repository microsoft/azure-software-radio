#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from gnuradio import gr_unittest
import azure_software_radio.default_credentials


class IntegrationDefaultCredentials(gr_unittest.TestCase):
    """
    Integration tests for default_credentials class
    """

    def test_environment_only(self):
        """
        Test authentication using environment vars only.
        """
        instance = azure_software_radio.default_credentials.get_default_creds(enable_cli_credential=False,
                                                                              enable_environment=True,
                                                                              enable_managed_identity=False,
                                                                              enable_powershell=False,
                                                                              enable_visual_studio_code=False,
                                                                              enable_shared_token_cache=False,
                                                                              enable_interactive_browser=False)
        n_creds = len(instance.credentials)
        self.assertEqual(n_creds, 1, f"Expected 1 credential, got: {n_creds} !")
        self.assertTrue('EnvironmentCredential' in str(instance.credentials[0]))

    def test_managed_identity_only(self):
        """
        Test authentication using managed identity only.
        """
        instance = azure_software_radio.default_credentials.get_default_creds(enable_cli_credential=False,
                                                                              enable_environment=False,
                                                                              enable_managed_identity=True,
                                                                              enable_powershell=False,
                                                                              enable_visual_studio_code=False,
                                                                              enable_shared_token_cache=False,
                                                                              enable_interactive_browser=False)
        n_creds = len(instance.credentials)
        self.assertEqual(n_creds, 1, f"Expected 1 credential, got: {n_creds} !")
        self.assertTrue('ManagedIdentityCredential' in str(instance.credentials[0]))


if __name__ == '__main__':
    gr_unittest.run(IntegrationDefaultCredentials)
