# Azure software radio examples

## Table of Contents
- [DIFI Examples](#difi-examples)
- [Key Vault Example](#key-vault-example)
- [Blob Examples](#blob-source-and-sink-examples)
- [Event Hub Examples](#event-hub-examples)

# DIFI Examples

The DIFI Source block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard. The example shows the use of the block in both paired and standalone mode. In paired mode, the DIFI sink is expected to be paired with a DIFI source block, else it will have unexpected behavior. If no DIFI source block is used, the DIFI sink block should be used in standalone mode. In standalone mode one must specify the fields that would have been in a context packet in paired mode. The examples show both of these situations.

- difi_paried_example: This will need an external DIFI source, either hardware or software that sends DIFI packets
- difi_standalone: This is expected to be run with samples coming from GNURadio and not an external DIFI source

# Key Vault Example

The Key Vault block pull the given key from an Azure Key Vault given the vault name.

In the example, you can see the correct way to input a value into the Azure Key Vault block.

To run the flowgraph correctly, you must setup a Key Vault resource in Azure and replace the KeyVault Name with your Key Vault resource name.

Also, the example assume you have the secretscramble key in your Key Vault. See https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli to get started with Key Vault


When your resources are ready in Azure, the flowgraph should pull the value from Azure Key Vault, and scramble the sequence with that pulled value.

If you want to enable the Azure Blob sink block, you will need to also setup a storage account and container in that account to store the data. The point of showing this is so that one can see how to use Azure Key Vault to get connection strings to use with Azure services, like Blob.

# Blob Source and Sink Examples
## Blob Example Prerequisites
To run [blob-sink-example.grc](../examples/blob-sink-example.grc) or [blob-source-example.grc](../examples/blob-source-example.grc), you must first create resources in Azure for the example files to interact with. 

You can either click the button below to deploy a new storage account and blob container for testing, or you can follow Azure tutorials on how to deploy the blob resources manually.

### Deploy Resources Automatically
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fpomeroy3%2Fazure-software-radio%2Ffeature%2Fautodeploy%2Fgr-azure-software-radio%2Fexamples%2Fblob_example_resources.json)

### Manual Resource Deployment Instructions
1. Set up a storage account in your Azure subscription
    - See: https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create
2. Add a container in that storage account.
    - See: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal#create-a-container

### Blob Authentication Options
You will need to choose how to authenticate to the blob storage account. This example is set up to use the "default" authentication option, which uses the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) to attempt to authenticate to the blob storage backend with a list of credential types in priority order.

The instructions below use the Azure CLI to configure access to Azure storage. See https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli to get started with the Azure CLI, or use the browser accessible Azure Cloud Shell to start using the AZ CLI without installing any dependencies: https://docs.microsoft.com/en-us/azure/cloud-shell/overview

If you are not using the Azure Cloud Shell, you will first need to log in to the Azure CLI:

```
az login
```

- If running on a VM in Azure, you may use the VM's Managed Identity for authentication. See https://docs.microsoft.com/en-us/azure/storage/blobs/authorize-managed-identity for more details on working with blobs and managed identities. This only needs to be set up for a given VM and storage account pairing once. Afterwards, the VM will have permissions to access any current or new blob containers in that storage account. 

    -  Check if your VM has a Manageed Identity by running:
        ```
        az vm identity show --name MyVirtualMachine --resource-group MyResourceGroup
        ```
        If there is a system assigned managed identity associated with the VM, you should see results that resemble the output below. 
        ```
        {
        "principalId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "tenantId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
        "type": "SystemAssigned",
        "userAssignedIdentities": null
        }
        ```
        
        If the VM has no associated managed identity, the command will not produce any output. In this case, you can enable a system-assigned managed identity on an existing Azure VM by running:

        ```
        az vm identity assign --name MyVirtualMachine --resource-group myResourceGroup
        ```
        If the command was successful, you should see results like the following:

        ```
        {
          "systemAssignedIdentity": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
          "userAssignedIdentities": {}
        }
        ```
        See https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/qs-configure-cli-windows-vm for more details on working with managed identities using the Azure CLI.

    -  Once you have confirmed that your VM has an associated managed identity, you can give the VM permissions to use the storage account.

        1. Get the service principal ID for the VM's managed identity by running:
            ```
            spID=$(az vm identity show --name MyVirtualMachine --resource-group myResourceGroup --query principalId --out tsv)
            ```
        2. Get the Azure ID of your storage account by running:
            ```
            storageID=$(az resource list --name MyStorageAccountName --query [*].id --out tsv)
            ```
        3. Give the VM full permissions to read and write to the storage account by assigning it the "Storage Blob Data Owner" role:
            ```
            az role assignment create --assignee $spID --role 'Storage Blob Data Owner' --scope $storageID
            ```

        See https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/howto-assign-access-cli for more details on using the Azure CLI to manage access to resources. 

- If the VM in Azure has managed identity disabled, or you are not running on an Azure VM, you may use the Azure CLI to log in to Azure and authenticate to blob storage. This only needs to be done once per user and storage account pairing. Afterwards, the user will have permissions to access any current or new blob containers in that storage account. 

    1. To log in to Azure, run:
        ``` 
        az login
        ```
    2. Ensure that you have assigned yourself the "Storage Blob Data Contributor" or "Storage Blob Data Owner" role for your storage account. Get the currently logged in user ID by running:
        ```
        userName=$(az ad signed-in-user show --query userPrincipalName --out tsv)
        ```
    3. Get the Azure ID of your storage account by running:
        ```
        storageID=$(az resource list --name MyStorageAccountName --query [*].id --out tsv)
        ```
    4. List what roles you have assigned for your storage account by running:
        ```
        az role assignment list --assignee $userName --scope $storageID --query [*].roleDefinitionName --out tsv
        ```
    5. If you do not see either the "Storage Blob Data Contributor" or "Storage Blob Data Owner" role for your storage account, add the "Storage Blob Data Owner" role by running:
        ```
        az role assignment create --assignee $userName --role 'Storage Blob Data Owner' --scope $storageID
        ```
    See https://docs.microsoft.com/en-us/azure/storage/blobs/assign-azure-role-data-access for more information on assigning roles to enable access to Azure storage resources.


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

Once you are done with running the examples, delete the resources you created to ensure you do not incur ongoing charges for storage.

# Event Hub Examples
## Event Hub Example Prerequisites
To run [eventhub_sink_example.grc](../examples/eventhub_sink_example.grc) or [eventhub_source_example.grc](../examples/eventhub-source-example.grc), you must first do the following:
1. Create an Event Hub in your Azure subscription
    - See: [Create an Event Hub](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-create) for instructions.
2. Create a Consumer Group in the Event Hub
    - See: [Create an Event Hub Consumer Group](https://docs.microsoft.com/en-us/cli/azure/eventhubs/eventhub/consumer-group?view=azure-cli-latest)
3. Choose how to authenticate to the Azure Event Hub. This example uses the "connection string" authentication option.
    - See [Get an Event Hub Connection String](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-get-connection-string) for instructions on how to obtain a connection string.

## Event Hub Sink Example
If you plan to use the Azure CLI to authenticate to the back end, please run

```bash
az login
```

and then launch GNU Radio Companion from the same terminal. This will ensure your authentication tokens are available when running the flowgraph. Open [eventhub_sink_example.grc](../examples/eventhub_sink_example.grc).

To run the flowgraph, you must:
- change the connection_str variable to use your connection string
- change the eventhub_name variable to use the event hub entity you created as part of the [Event Hub Prerequisites section above](#event-hub-example-prerequisites)

Run the flowgraph for a few seconds and then close it. Navigate to your event hub in the Azure portal and you should see the events in the 'overview' tab. To process the events, enable the real-time insights under 'process data'.

## Event Hub Source Example
If you plan to use the Azure CLI to authenticate to the back end, please run

```bash
az login
```

and then launch GNU Radio Companion from the same terminal. This will ensure your authentication tokens are available when running the flowgraph. Open [eventhub_source_example.grc](../examples/eventhub_source_example.grc).

To run the flowgraph, you must:
- change the connection_str variable to use your connection string
- change the eventhub_name variable to use the event hub entity you created as part of the [Event Hub Prerequisites section above](#event-hub-example-prerequisites)
- change the consumer_grp variable to use the default or use the created consumer group as part of the [Event Hub Prerequisites section above](#event-hub-example-prerequisites)

Run the flowgraph and you should see the Message Debug block showing the contents of the received events.

