# Azure Authentication with DefaultAzureCredentials and Managed Identities

Many of the examples for this Out-of-Tree module require the configuration of Azure services to work properly. This
quickstart will walk through how to use the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) to configure [managed identities](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
to enable applications running in Azure VMs to authenticate to Azure resources.

## Prerequisites
- You must run the examples on a Virtual Machine in Azure.

- Use the Bash environment in [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart).
For more information, see [Azure Cloud Shell Quickstart - Bash](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart)

    [![Launch Cloud Shell](hdi-launch-cloud-shell.png "Launch Cloud Shell")](https://shell.azure.com)

- If you prefer to run CLI reference commands locally, [install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) the Azure CLI. If you are running on Windows or macOS, consider running Azure CLI in a Docker container. For more information, see [How to run the Azure CLI in a Docker container](https://docs.microsoft.com/en-us/cli/azure/run-azure-cli-docker).

    - If you're using a local installation, sign in to the Azure CLI by using the [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login) command. To finish the authentication process, follow the steps displayed in your terminal. For additional sign-in options, see [Sign in with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli).

    - When you're prompted, install Azure CLI extensions on first use. For more information about extensions, see [Use extensions with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/azure-cli-extensions-overview).

    - Run [az version](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_version) to find the version and dependent libraries that are installed. To upgrade to the latest version, run [az upgrade](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_upgrade).

- This article requires version 2.29.0 or later of the Azure CLI. If using Azure Cloud Shell, the latest version is already installed.

## Set the subscription context
The following steps are not required if you're running commands in Cloud Shell. If you're running the CLI locally, perform the following steps to sign in to Azure and set your current subscription:

Set the current subscription context. Replace `MyAzureSub` with the name of the Azure subscription you want to use:

```
az account set --subscription MyAzureSub
```

## Confirm that your virtual machine has a system-assigned managed identity
You can choose to have a system-assigned managed identity associated with your virtual machine when it is first created.
Check if the virtual machine that you'll use to run the examples has a managed identity by running:

```
az vm identity show --name MyVirtualMachine --resource-group MyResourceGroup
```

If there is a managed identity already associated with your virtual machine, you should see output resembling:

```
{
"principalId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
"tenantId": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
"type": "SystemAssigned",
"userAssignedIdentities": null
}
```

If there is no managed identity associated with your virtual machine, the command will not generate any output.

## Assign a managed identity to a virtual machine
If your virtual machine does not have a managed identity associate with it, you can [Configure managed identities for Azure resources on a VM using the Azure portal](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/qs-configure-portal-windows-vm)
or you can configure one with the commands below:

```
az vm identity assign --name MyVirtualMachine --resource-group myResourceGroup
```

If the command was successful, you should see results like:

```
{
    "systemAssignedIdentity": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
    "userAssignedIdentities": {}
}
```

See [Configure managed identities for Azure resources on an Azure VM using Azure CLI](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/qs-configure-cli-windows-vm) for more details on working with managed identities
using the Azure CLI.

----
## Recommended content

### [az vm identity](https://docs.microsoft.com/en-us/cli/azure/vm/identity)

### [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/)

### [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart)
