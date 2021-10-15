# Azure software radio examples

## Table of Contents
- [DIFI Examples](#difi-examples)
- [Key Vault Example](#key-vault-example)
- [Blob Examples](#blob-source-and-sink-examples)

# DIFI Examples

The DIFI Source block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard. The example shows the use of the block in both paired and standalone mode. In paired mode, the DIFI sink is expected to be paired with a DIFI source block, else it will have unexpected behavior. If no DIFI source block is used, the DIFI sink block should be used in standalone mode. In standalone mode one must specify the fields that would have been in a context packet in paired mode. The examples show both of these situations.

# Key Vault Example

The Key Vault block pulls given keys from a Azure Key Vault given the vault name. If a list element is a string, that string is the key that will be pulled and the key is also the name of the variable set in GRC. If a list element is a tuple, the first item of the tuple is the key that will be pulled and the second element is the name of variable in GRC.

In the example, you can see the correct way to input values into the Azure Key Vault block, both tuple and no tuple (renaming). 

To run the flowgraph correctly, you must setup a Key Vault resource in Azure and replace the KeyVault Name with your Key Vault resource name. 

Also, the example assume you have seed, secretscramble, and mysecretstring keys in your Key Vault. See https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli to get started with Key Vault


When your resources are ready in Azure, the flowgraph should pull the values from Azure Key Vault, and scramble the sequence with those pulled values.

If you want to enable the Azure Blob sink block, you will need to also setup a storage account and container in that account to store the data. The point of showing this is so that one can see how to use Azure Key Vault to get connection strings to use with Azure services, like Blob. 
    
# Blob Source and Sink Examples
## Blob Example Prerequisites
To run [blob-sink-example.grc](../examples/blob-sink-example.grc) or [blob-source-example.grc](../examples/blob-source-example.grc), you must first:
1. Set up a storage account in your Azure subscription
    - See: https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create 
2. Add a container in that storage account. 
    - See: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal#create-a-container 
3. Choose how to authenticate to the blob storage account. This example uses the "default" authentication option, which uses the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) to attempt to authenticate to the blob storage backend with a list of credential types in priority order.  
    - If running on a VM in Azure, you may use the VM's Managed Identity for authentication. See https://docs.microsoft.com/en-us/azure/storage/blobs/authorize-managed-identity for instructions on how to work with blobs and managed identities.     
    - If the VM in Azure has managed identity disabled, or not running on an Azure VM, you may use the Azure CLI to log in to Azure and authenticate to blob storage.
        - See https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli to get started
        with the Azure CLI. 
        - Ensure that you have assigned yourself the "Storage Blob Data Contributor" permission for
        your storage account. See https://docs.microsoft.com/en-us/azure/storage/blobs/assign-azure-role-data-access

## Blob Sink Example
If you plan to use the Azure CLI to authenticate to the blob back end, please run 

```bash
az login
```

and then launch GNU Radio Companion from the same terminal. This will ensure your authentication tokens are available when running the flowgraph. Open [blob-sink-example.grc](../examples/blob-sink-example.grc). 

To run the flowgraph, you must:
- change the blob_url variable to use your actual storage account URL
- change the blob_container_name variable to use the container name you created as part of the [Blob Prerequisites section above](#blob-example-prerequisites)

Run the flowgraph until at least `blob_block_length` (defaults to 10M) samples have been generated, then close the flowgraph. Navigate to your blob container in the Azure portal and you should see a new blob object named "test-signal.dat". 

## Blob Source Example
If you plan to use the Azure CLI to authenticate to the blob back end, please run 

```bash
az login
```

and then launch GNU Radio Companion from the same terminal. This will ensure your authentication tokens are available when running the flowgraph. Open [blob-source-example.grc](../examples/blob-source-example.grc).

To run the flowgraph, you must:
- change the blob_url variable to use your actual storage account URL
- change the blob_container_name variable to use the container name you created as part of the [Blob Prerequisites section above](#blob-example-prerequisites)
- change the blob_name to point to an existing blob object. The simplest way to create a blob object is to run the (Blob Sink Example)(#blob-sink-example) first.

Run the flowgraph and you should see the QT GUI Sink block showing the contents of your blob object.

Once you are done with running the examples, delete your blob object to stop being charged for storage. 
