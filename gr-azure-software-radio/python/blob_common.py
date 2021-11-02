# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def get_blob_service_client(authentication_method: str = "default", connection_str: str = None,
                            url: str = None):
    """ Initialize the blob service client

    Args:
        authentication_method (str): Determines which method to use to authenticate to the
            Azure blob backend. May be one of "connection_string", "url_with_sas", or "default".
        connection_str (optional, str): Azure storage account connection string used for
            authentication if authentication_method is "connection_string"
        url (optional, str): Storage account URL. This is required if using "default" or
            "url_with_sas" authentication. If using "url_with_sas", the URL must include a SAS
            token.

    Raises:
        ValueError: Raised if an unsupported authentication method is used

    Returns:
        BlobServiceClient: A blob service client ready to be used to create blob client objects
    """
    if authentication_method == "connection_string":
        blob_service_client = BlobServiceClient.from_connection_string(connection_str)

    elif authentication_method == "url_with_sas":
        blob_service_client = BlobServiceClient(account_url=url)

    # no connection string was specified, try to use the DefaultAzureCredential
    elif authentication_method == "default":

        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=url,
                                                credential=default_credential)
    else:
        raise ValueError("Unsupported authentication method specified")

    return blob_service_client


def shutdown_blob_service_client(service_client: BlobServiceClient):
    """Close the blob service client
    Args:
        service_cliient: The blob service client to close
    Raises:
        None
    Returns:
        None
    """
    service_client.close()
