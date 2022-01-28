# Azure software radio examples

## Table of Contents
- [DIFI Examples](#difi-examples)
- [Azure Authentication](#azure-authentication)
- [Key Vault Example](#key-vault-example)
- [Blob Examples](#blob-source-and-sink-examples)
- [Event Hub Examples](#event-hub-examples)

# DIFI Examples

The DIFI Source block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard. The example shows the use of the block in both paired and standalone mode. In paired mode, the DIFI sink is expected to be paired with a DIFI source block, else it will have unexpected behavior. If no DIFI source block is used, the DIFI sink block should be used in standalone mode. In standalone mode one must specify the fields that would have been in a context packet in paired mode. The examples show both of these situations.

- difi_paried_example: This will need an external DIFI source, either hardware or software that sends DIFI packets
- difi_standalone: This is expected to be run with samples coming from GNURadio and not an external DIFI source


# Azure Authentication
Most of the examples below use the Azure CLI to configure access to Azure services. See https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli to get started with the Azure CLI, or use the browser accessible Azure Cloud Shell to start using the AZ CLI without installing any dependencies: https://docs.microsoft.com/en-us/azure/cloud-shell/overview

Several of the examples below use the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) to authenticate to Azure. The DefaultAzureCredential class attempts to authenticate to Azure using a list of credential types in priority order. The examples below will focus on using the ManagedIdentityCredential or AzureCliCredential credential types supported by the DefaultAzureCredential classes. Some examples may also use credentials such as Connection Strings instead of the DefaultAzureCredential.

- If you are running these example flowgraphs on a VM in Azure, you may use the VM's managed identity for authentication. Managed identities eliminate the need for developers to manage credentials in their applications. See https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview for an overview of using managed identities in Azure.

    -  Check if your VM has a managed identity by logging in to the Azure CLI and running:
        ```
        az login
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

- If you are running these examples on a VM in Azure that does not use a managed identity, or you are not running on an Azure VM, you may use the Azure CLI to authenticate to Azure services at the start of your session. To log in to Azure, run:
    ```
    az login
    ```

# Key Vault Example

The Key Vault block is used to retrieve secrets stored in Azure Key Vault. These secrets are stored as strings and are looked up by name.

In the example, you can see the correct way to input a value into the Azure Key Vault block.

To run the flowgraph correctly, you must setup a Key Vault resource in Azure and use it to store several secret values. You'll need to update the Key Vault name in the example flowgraph with the Key Vault name you choose when you deploy your Azure resources.

You can either click the button below to deploy a new Key Vault for testing, or you can follow Azure tutorials on how to deploy the Key Vault and set up secrets manually.

## Deploy Resources Automatically
Click the following button to deploy a Key Vault with Role Based Access Controls (RBAC) and populate secrets for the example:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](fixme-url-encoded-path.json)

## Deploy Resources Manually
If you'd prefer to get started with Key Vault by manually configuring your resources, see https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli. When creating the Key Vault, make sure to enable RBAC by using the `--enable-rbac-authorization` flag, like:

```
az keyvault create --name "<your-unique-keyvault-name>" --resource-group "myResourceGroup" --location "EastUS" --enable-rbac-authorization true
```

If you would prefer to use a Vault access policy permission model, create the Key Vault with `--enable-rbac-authorization false` and follow https://docs.microsoft.com/en-us/azure/key-vault/general/assign-access-policy to configure the Key Vault Access policy.

### Secrets
 You'll need to add at least two secrets to your new Key Vault before you can successfully run the flowgraph:

- seed: Integer random seed to use as an initial shift register contents for a scrambling algorithm.
- scramble: Integer valued polynomial mask for the scrambling algorithm LFSR
- mysecretstring: Optional - If you want to enable the blob sink block, you'll need to configure a storage account and blob container, then store the blob container's connection string in this secret.

Create these secrets by following the instructions at https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli.

## Assign Permissions
Assuming you've enabled the RBAC permission model for your Key Vault, you'll need to assign roles to be able to access the Key Vault. You'll need to know the role name you want to assign, the assignee to assign this role to, and the scope over which to assign this role. It's considered a best practice to grant access with the least privilege that is needed, so avoid assigning a role at a broader scope than necessary. See https://docs.microsoft.com/en-us/azure/key-vault/general/rbac-guide?tabs=azure-cli and https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-cli for more details.

- If you are running the example flowgraph on a VM with a managed identity enabled, you can assign an RBAC role to the VM's identity. See [Azure Authentication](#azure-authentication) above to see if your VM has a managed identity. To assign a role to your VM's identity:

    1. Get the service principal ID for the VM's managed identity by running:
        ```
        spID=$(az vm identity show --name MyVirtualMachine --resource-group myResourceGroup --query principalId --out tsv)
        ```
    2. Get the Azure ID of your Key Vault by running:
        ```
        kvID=$(az resource list --name MyKeyVaultName --query [*].id --out tsv)
        ```
    3. Give the VM permissions to read and write to the Key Vault's secrets by assigning it the "Key Vault Secrets Officer" role:
        ```
        az role assignment create --assignee $spID --role 'Key Vault Secrets Officer' --scope $kvID
        ```

- If you are running the example flowgraph on a VM in Azure that has managed identity disabled, or you are not running on an Azure VM, you can assign an RBAC role to your own user identity and authenticate with the Azure CLI before running the flowgraph.

    1. Get your current user ID in Azure:
        ```
        userName=$(az ad signed-in-user show --query userPrincipalName --out tsv)
        ```
    2. Get the Azure ID of your Key Vault by running:
        ```
        kvID=$(az resource list --name MyKeyVaultName --query [*].id --out tsv)
        ```
    3. Give the VM permissions to read and write to the Key Vault's secrets by assigning it the "Key Vault Secrets Officer" role:
        ```
        az role assignment create --assignee $userName --role 'Key Vault Secrets Officer' --scope $kvID
        ```


## Flowgraph Update
When your resources are ready in Azure, update the `key_vault_name` variable in the Key Vault example flowgraph to the name you chose for your
deployed Key Vault. Once properly configured, the flowgraph should pull the value from Azure Key Vault, and scramble the sequence with that pulled value.

If you want to enable the Azure Blob sink block, you will need to also setup a storage account and container in that account to store the data. See https://docs.microsoft.com/en-us/azure/storage/common/storage-configure-connection-string for details on connection strings. The point of showing this is so that one can see how to use Azure Key Vault to get connection strings to use with Azure services, like Blob.

If you are not running the flowgraph on a VM with managed identity enabled, run `az login` and then start GNU Radio Companion from the same terminal to ensure GNU Radio has access to your credentials.

# Blob Source and Sink Examples
## Blob Example Prerequisites
To run [blob-sink-example.grc](../examples/blob-sink-example.grc) or [blob-source-example.grc](../examples/blob-source-example.grc), you must first create resources in Azure for the example files to interact with.

You can either click the button below to deploy a new storage account and blob container for testing, or you can follow Azure tutorials on how to deploy the blob resources manually.

### Deploy Resources Automatically
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fazure-software-radio%2Fdocumentation%2Fcli-updates%2Fgr-azure-software-radio%2Fexamples%2Fblob_example_resources.json)

### Deploy Resources Manually
1. Set up a storage account in your Azure subscription
    - See: https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create
2. Add a container in that storage account.
    - See: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal#create-a-container

### Blob Authentication Options
You will need to choose how to authenticate to the blob storage account. This example is set up to use the "default" authentication option, which uses the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) to attempt to authenticate to the blob storage backend with a list of credential types in priority order.

The instructions below use the Azure CLI to configure access to Azure storage. See https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli to get started with the Azure CLI, or use the browser accessible Azure Cloud Shell to start using the AZ CLI without installing any dependencies: https://docs.microsoft.com/en-us/azure/cloud-shell/overview


- If you are running the example flowgraph on a VM with a managed identity enabled, you can give the VM permissions to use the storage account.

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
To run [eventhub_sink_example.grc](../examples/eventhub_sink_example.grc) or [eventhub_source_example.grc](../examples/eventhub-source-example.grc), you must first create an Event Hub namespace, an Event Hub, and a consumer group. To deploy these resources, either click the 'Deploy to Azure' button or follow the manual deployment instructions below:

### Deploy Resources Automatically
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](fixme-url-encoded-path.json)

### Deploy Resources Manually
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

See the instructions on how to [Get an Event Hubs connection string](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-get-connection-string) for more details.

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
- change the consumer_grp variable to use consumer group created as part of the [Event Hub Prerequisites section above](#event-hub-example-prerequisites)

See the instructions on how to [Get an Event Hubs connection string](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-get-connection-string) for more details.

Run the flowgraph and you should see the Message Debug block showing the contents of the received events.

