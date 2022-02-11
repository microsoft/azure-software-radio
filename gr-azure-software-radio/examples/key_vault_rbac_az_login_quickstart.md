# Quickstart: Key Vault with Role Based Access Controls and Azure CLI Credentials

The Key Vault block is used to retrieve secrets stored in Azure Key Vault. These secrets are stored as strings and are looked up by name, making credential management much more secure. The steps in this article will work for interactive sessions on
systems with access to Azure.


In this article you learn how to:
- Deploy an Azure Key Vault with a [role-based access control (Azure RBAC)](https://docs.microsoft.com/en-us/azure/role-based-access-control/overview) permissions model.
- Add secrets to a Key Vault using Azure CLI.
- Assign a role to a specific user in [Azure Active Directory](https://docs.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-whatis).
- Provide credentials to an application at runtime using the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) and the [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login) command.

## Prerequisites
- Use the Bash environment in [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart).
For more information, see [Azure Cloud Shell Quickstart - Bash](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart)

    <a href="https://shell.azure.com"><img src="hdi-launch-cloud-shell.png"></a>

- If you prefer to run CLI reference commands locally, [install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) the Azure CLI. If you are running on Windows or macOS, consider running Azure CLI in a Docker container. For more information, see [How to run the Azure CLI in a Docker container](https://docs.microsoft.com/en-us/cli/azure/run-azure-cli-docker).

    - If you're using a local installation, sign in to the Azure CLI by using the [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login) command. To finish the authentication process, follow the steps displayed in your terminal. For additional sign-in options, see [Sign in with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli).

    - When you're prompted, install Azure CLI extensions on first use. For more information about extensions, see [Use extensions with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/azure-cli-extensions-overview).

    - Run [az version](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_version) to find the version and dependent libraries that are installed. To upgrade to the latest version, run [az upgrade](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_upgrade).

- This article requires version 2.29.0 or later of the Azure CLI. If using Azure Cloud Shell, the latest version is already installed.
- You must [install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) the Azure CLI on the machine that will run the example flowgraph.
- If running on a virtual machine in Azure, you must **not** enable a managed identity. The Key Vault block uses the DefaultAzureCredential class for authentication, which will use the managed identity for authentication if it is enabled, ignoring credentials provided by [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login). Follow [these instructions](managed_identity_cli_quickstart.md) to confirm whether or not your virtual machine has a managed identity enabled.

## Deploy a Key Vault and configure secrets
To run the flowgraph correctly, you must setup a Key Vault resource in Azure and use it to store several secret values. You'll need to update the Key Vault name in the example flowgraph with the Key Vault name you choose when you deploy your Azure resources.

### Deploy Resources Automatically
Click the following button to deploy a Key Vault with Role Based Access Controls (RBAC) and populate secrets for the example:

<a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fazure-software-radio%2Fdev%2Fgr-azure-software-radio%2Fexamples%2Fkey_vault_example_resources.json" target="_blank"><img src="https://aka.ms/deploytoazurebutton"></a>

### Deploy Resources Manually
If you'd prefer to get started with Key Vault by manually configuring your resources, you can follow this guide to [set and retrieve a secret from Azure Key Vault using Azure CLI](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli). When creating the Key Vault, you must make sure to enable RBAC by using the `--enable-rbac-authorization` flag, like:

```
az keyvault create --name "<your-unique-keyvault-name>" --resource-group "myResourceGroup" --location "EastUS" --enable-rbac-authorization true
```

## Add secrets to Key Vault
 You'll need to add at least two secrets to your new Key Vault before you can successfully run the flowgraph:

- seed: Integer random seed to use as an initial shift register contents for a scrambling algorithm.
- scramble: Integer valued polynomial mask for the scrambling algorithm LFSR
- mysecretstring: Optional - If you want to enable the blob sink block, you'll need to configure a storage account and blob container, then store the blob container's connection string in this secret.

Create these secrets by following the instructions on how to [set and retrieve a secret from Azure Key Vault using Azure CLI](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli)

## Assign a Key Vault Role to your Azure identity
You need to assign the appropriate role to your Azure identity for your application to be able to access the Key Vault using credentials credentials provided by [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login). You'll need to know the role name you want to assign, the assignee to assign this role to, and the scope over which to assign this role. It's considered a best practice to grant access with the least privilege that is needed, so avoid assigning a role at a broader scope than necessary. See how to [Provide access to Key Vault keys, certificates, and secrets with an Azure role-based access control](https://docs.microsoft.com/en-us/azure/key-vault/general/rbac-guide?tabs=azure-cli) and how to [Assign Azure roles using Azure CLI](https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-cli) for more details.

If running on a virtual machine in Azure, you must **not** enable a managed identity. The Key Vault block uses the DefaultAzureCredential class for authentication, which will use the managed identity for authentication if it is enabled, ignoring credentials provided by `az login`.

Confirm that your virtual machine does not have managed identity enabled by following [these instructions](managed_identity_cli_quickstart.md).

To assign a role to your Azure identity, first get your current user ID in Azure:
```
userName=$(az ad signed-in-user show --query userPrincipalName --out tsv)
```

Next get the Azure ID of your Key Vault by running:
```
kvID=$(az resource list --name MyKeyVaultName --query [*].id --out tsv)
```

Finally, give the VM permissions to read and write to the Key Vault's secrets by assigning it the "Key Vault Secrets Officer" role:
```
az role assignment create --assignee $userName --role 'Key Vault Secrets Officer' --scope $kvID
```

## Flowgraph Update
When your resources are ready in Azure, update the `key_vault_name` variable in the Key Vault example flowgraph to the name you chose for your
deployed Key Vault. Once properly configured, the flowgraph should pull the value from Azure Key Vault, and scramble the sequence with that pulled value.

If you want to enable the Azure Blob sink block, you will need to also setup a storage account and container in that account to store the data. See https://docs.microsoft.com/en-us/azure/storage/common/storage-configure-connection-string for details on connection strings. The point of showing this is so that one can see how to use Azure Key Vault to get connection strings to use with Azure services, like Blob.

If you are not running the flowgraph on a VM with managed identity enabled, run `az login` and then start GNU Radio Companion from the same terminal to ensure GNU Radio has access to your credentials.

## Run the flowgraph
You will need to [sign in with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli) on the
machine where you intend to run the example flowgraph. After signing in, you will need to launch GNU Radio Companion
from the same terminal session to ensure the example flowgraph has access to the authentication token generated by the
`az login` command.

Run the flowgraph in GNU Radio Companion. The Key Vault block will use the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity) ti access the authentication token generated by the `az login` command and use it to authenticate to Key Vault.


----
## Recommended content

### [Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/general/overview)
### [Assign a Key Vault access policy](https://docs.microsoft.com/en-us/azure/key-vault/general/assign-access-policy?tabs=azure-cli)
### [DefaultAzureCredential class](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python)







