# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
import logging

import azure.core.exceptions as az_exceptions
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from gnuradio import gr


def get_blob_service_client(authentication_method: str = "default", connection_str: str = None,
                            url: str = None, retry_total=10):
    """ Initialize the blob service client

    Args:
        authentication_method (str): Determines which method to use to authenticate to the
            Azure blob backend. May be one of "connection_string", "url_with_sas", or "default".
        connection_str (optional, str): Azure storage account connection string used for
            authentication if authentication_method is "connection_string"
        url (optional, str): Storage account URL. This is required if using "default" or
            "url_with_sas" authentication. If using "url_with_sas", the URL must include a SAS
            token.
        retry_total (int, optional): Total number of Azure API retries to allow

    Raises:
        ValueError: Raised if an unsupported authentication method is used

    Returns:
        BlobServiceClient: A blob service client ready to be used to create blob client objects
    """
    if authentication_method == "connection_string":
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_str, retry_total=retry_total)

    elif authentication_method == "url_with_sas":
        blob_service_client = BlobServiceClient(
            account_url=url, retry_total=retry_total)

    # no connection string was specified, try to use the DefaultAzureCredential
    elif authentication_method == "default":
        # dial down the logging level for the DefaultAzureCredential to prevent it
        # from being overly chatty about which credentials it was using
        az_id_log = logging.getLogger('azure.identity')
        az_id_log.setLevel(logging.CRITICAL)
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=url, credential=default_credential, retry_total=retry_total)
    else:
        raise ValueError("Unsupported authentication method specified")

    return blob_service_client


def blob_container_info_is_valid(blob_service_client, container_name):
    '''
    Do some checks against the blob info we've been provided so we can add log messages with
    extra context
    '''
    log = gr.logger("log_debug")

    log.debug("Validating blob configuration info")
    try:

        container_client = blob_service_client.get_container_client(container=container_name)

        if not container_client.exists():
            err = az_exceptions.ResourceNotFoundError(
                f"Blob Container '{container_name}' does not exist")
            log.error(f"{err}")
            raise err

    except az_exceptions.ServiceRequestError as err:
        log.error(
            "Blob block could not connect to the storage account using the URL or connection "
            + "string provided")
        log.error(f"{err}")
        raise err

    except az_exceptions.ClientAuthenticationError as err:
        log.error(
            "Blob block could not authenticate to blob storage with the credentials provided")
        log.error(f"{err}")
        raise err

    except Exception as err:
        log.error(f"{err}")
        raise err

    return True


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
