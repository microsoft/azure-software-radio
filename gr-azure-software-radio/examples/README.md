# Azure software radio examples

Below you will find examples for each block within this OOT module.

## Table of Contents
- [DIFI Examples](#difi-source-and-sink-examples)
- [Azure Authentication](#azure-authentication)
- [Key Vault](#key-vault)
- [Blob Storage](#blob-storage)
- [Event Hub](#event-hub)
- [REST API](#rest-api)


## DIFI Source and Sink Examples
The intent of the Digital Intermediate Frequency Interoperability (DIFI) standard is to enable the digital transformation
of space, satellite, and related industries by providing a simple, open, interoperable Digital IF/RF standard that
replaces the natural interoperability of analog IF signals and helps prevent vendor lock-in. The articles linked below
describe how to run the examples which show how to use the DIFI source and sink blocks that implement the DIFI standard
for use with GNU Radio.

- [Quickstart: Running the DIFI source and sink block examples](difi_quickstart.md)

## Azure Authentication
The remaining examples below require the use Azure resources, most of which require applications to authenticate to them
in some way before they can be used. Most of the GNU Radio blocks in the Azure software radio Out-of-Tree module support
 the use of the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python), which supports a wide variety of credential types, as one of their
 authentication methods. In general, the examples below try to show how to use the blocks in the Azure software radio
Out-of-Tree module in applications running on resources in Azure as well as in on premise hardware, such as developer
systems or edge-deployed servers. [Azure managed identities](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview) can be convenient credentials for use in applications running in Azure,
while credentials retrieved by [signing in using the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli) can be used interactively from any system with access to Azure.

The article below walks through how to enable a managed identity on a virtual machine in Azure so that applications
running on that VM can authenticate to other Azure resources.

- [Azure Managed Identity Configuration with the Azure CLI](managed_identity_cli_quickstart.md)
## Key Vault

The Key Vault block is used to retrieve secrets stored in Azure Key Vault, and these two quickstarts show how they can be used within GNU Radio.

- [Quickstart: Key Vault with Role Based Access Controls and Azure CLI Credentials](key_vault_rbac_az_login_quickstart.md)
- [Quickstart: Key Vault with Role Based Access Controls and Managed Identities](key_vault_rbac_managed_id_quickstart.md)

## Blob Storage
Many GNU Radio applications involve working with files, and the Blob Source and Sink blocks allow files to be stored and retrieved from Azure with ease.  The following quickstarts show how to use these blocks, depending on whether you are on a VM with Managed ID enabled, or are using `az login`.

- [Quickstart: Running the Blob Source and Sink blocks with Managed ID](blob_managed_id_quickstart.md)
- [Quickstart: Running the Blob Source and Sink blocks with `az login`](blob_az_login_quickstart.md)

## Event Hub
The Event Hub blocks provide an interface to send and receive events to Azure Event Hubs using the message passing interface in GNU Radio. The article below walks through examamples of both the Source and Sink blocks.

- [Quickstart: Using Azure Event Hubs in GNU Radio](event_hubs_quickstart_cli.md)


## REST API
The REST API Block hosts a REST API server which allows getting status from a flowgraph, configuring variables, and calling functions as specified in the readable and writable block params. The following quickstart shows how to use this block.

- [Quickstart: Using REST API in GNU Radio](rest_api_quickstart.md)
