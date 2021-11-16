# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, duplicate-code
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

"""
Integration tests for functions from blob_common.py
"""
import os
import azure_software_radio
from gnuradio import gr_unittest
from azure_software_radio import blob_common


class IntegrationBlobCommon(gr_unittest.TestCase):
    """ Test case class for running integration tests on blob_common.py
    """

    # pylint: disable=invalid-name
    def setUp(self):
        azure_software_radio.blob_setup(self)

    # pylint: disable=invalid-name
    def tearDown(self):
        azure_software_radio.blob_teardown(self)

    def test_connection_string_auth(self):
        '''
        Test that connection string authentication works. You must have the
        AZURE_STORAGE_CONNECTION_STRING environment variable defined with a valid connection
        string for this to pass
        '''

        blob_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = blob_common.get_blob_service_client(
            authentication_method="connection_string",
            connection_str=blob_connection_string
        )

        svc_props = blob_service_client.get_service_properties()

        blob_service_client.close()
        self.assertIsNotNone(svc_props)

    def test_url_with_sas_auth(self):
        '''
        Test that authentication using a URL with a SAS token works. You must have the
        AZURE_STORAGE_URL environment variable defined with the URL to a valid storage account
        and AZURE_STORAGE_SAS environment variable defined with an active SAS token with read access
        to the storage account for this to pass
        '''

        url = os.getenv('AZURE_STORAGE_URL')
        sas = os.getenv('AZURE_STORAGE_SAS')

        blob_service_client = blob_common.get_blob_service_client(
            authentication_method="url_with_sas",
            url=url + '/' + sas
        )

        svc_props = blob_service_client.get_service_properties()

        blob_service_client.close()
        self.assertIsNotNone(svc_props)

    def test_default_auth(self):
        '''
        Test that authentication using one of the valid DefaultAzureCredentials. You must be running
        this test on a system with a managed identity, environment variables configured according to
        https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=azure-python#environment-variables
        or by running `az login` before a test. You must also have an AZURE_STORAGE_URL environment
        variable defined with the URL to a valid storage account
        '''

        url = os.getenv('AZURE_STORAGE_URL')
        blob_service_client = blob_common.get_blob_service_client(url=url)

        svc_props = blob_service_client.get_service_properties()

        blob_service_client.close()
        self.assertIsNotNone(svc_props)


if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobCommon)