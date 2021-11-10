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

import azure.core.exceptions as az_exceptions
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

    def test_bad_storage_account(self):
        '''
        Check that the code raises the appropriate exception in response to being given a storage
        account URL that doesn't exist
        '''
        url = "https://invalid_url.blob_doesnt_exist.core.windows.net"
        sas = os.getenv('AZURE_STORAGE_SAS')

        blob_service_client = blob_common.get_blob_service_client(
            authentication_method="url_with_sas",
            url=url + '/' + sas,
            retry_total=0
        )

        with self.assertRaises(az_exceptions.ServiceRequestError):
            blob_common.blob_container_info_is_valid(blob_service_client=blob_service_client,
                                                     container_name="does-not-exist")

    def test_bad_authentication(self):
        '''
        Check that the code raises the appropriate exception in response to being given a valid
        storage account URL but bad authentication info
        '''
        url = os.getenv('AZURE_STORAGE_URL')
        sas = os.getenv('AZURE_STORAGE_SAS')

        # force the SAS token to be wrong
        if sas[-1] == 'A':
            bad_sas = sas[:-1] + 'B'
        else:
            bad_sas = sas[:-1] + 'A'

        blob_service_client = blob_common.get_blob_service_client(
            authentication_method="url_with_sas",
            url=url + '/' + bad_sas,
            retry_total=0
        )

        with self.assertRaises(az_exceptions.ClientAuthenticationError):
            blob_common.blob_container_info_is_valid(blob_service_client=blob_service_client,
                                                     container_name="does-not-exist")

    def test_missing_container(self):
        '''
        Check that the code raises the appropriate exception in response to being given a container
        name that doesn't exist
        '''
        url = os.getenv('AZURE_STORAGE_URL')
        sas = os.getenv('AZURE_STORAGE_SAS')

        blob_service_client = blob_common.get_blob_service_client(
            authentication_method="url_with_sas",
            url=url + '/' + sas,
            retry_total=0
        )

        with self.assertRaises(az_exceptions.ResourceNotFoundError):
            blob_common.blob_container_info_is_valid(blob_service_client=blob_service_client,
                                                     container_name="does-not-exist")


if __name__ == '__main__':
    gr_unittest.run(IntegrationBlobCommon)
