# Quickstart: Running the Blob Source and Sink blocks with az login

In this article you learn how to:
- Create a blob storage account and container
- Authenticate to the blob storage account from within GNU Radio
- Simulate a signal in GNU Radio which then gets stored as a blob
- Pull down the previously stored signal from blob storage and feed it through a GNU Radio flowgraph

The steps in this article will work for interactive sessions on systems with access to Azure.

## Prerequisites
- Use the Bash environment in [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart).
For more information, see [Azure Cloud Shell Quickstart - Bash](https://docs.microsoft.com/en-us/azure/cloud-shell/quickstart)

    [![Launch Cloud Shell](hdi-launch-cloud-shell.png "Launch Cloud Shell")](https://shell.azure.com)

- If you prefer to run CLI reference commands locally, [install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) the Azure CLI. If you are running on Windows or macOS, consider running Azure CLI in a Docker container. For more information, see [How to run the Azure CLI in a Docker container](https://docs.microsoft.com/en-us/cli/azure/run-azure-cli-docker).

    - If you're using a local installation, sign in to the Azure CLI by using the [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login) command. To finish the authentication process, follow the steps displayed in your terminal. For additional sign-in options, see [Sign in with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli).

    - When you're prompted, install Azure CLI extensions on first use. For more information about extensions, see [Use extensions with the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/azure-cli-extensions-overview).

    - Run [az version](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_version) to find the version and dependent libraries that are installed. To upgrade to the latest version, run [az upgrade](https://docs.microsoft.com/en-us/cli/azure/reference-index?#az_upgrade).

- This article requires version 2.29.0 or later of the Azure CLI. If using Azure Cloud Shell, the latest version is already installed.
- You must [install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) the Azure CLI on the machine that will run the example flowgraph.
- If running on a virtual machine in Azure, you must **not** enable a managed identity. The Key Vault block uses the DefaultAzureCredential class for authentication, which will use the managed identity for authentication if it is enabled, ignoring credentials provided by [az login](https://docs.microsoft.com/en-us/cli/azure/reference-index#az_login). Follow [these instructions](managed_identity_cli_quickstart.md) to confirm whether or not your virtual machine has a managed identity enabled.

## Set Up Storage in Azure

To run the examples in this quickstart you must first create the necessary resources in Azure.  You can either click the button below to deploy a new storage account and blob container for testing, or you can follow Azure tutorials on how to deploy the blob resources manually.

(Choose One)

1. Deploy Resources Automatically

    1. Click [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fazure-software-radio%2Fdocumentation%2Fcli-updates%2Fgr-azure-software-radio%2Fexamples%2Fblob_example_resources.json)
    2. You will have to pick a new or existing resource group to assign the new resources to
    3. The default value for Storage Account Name might look confusing but if you leave it as is, it will create a new one with a globally unique name to avoid conflicts, such as storageaccountgeh5jwaddf7tc.  You are welcome to replace the entire string with your own unique name, it may contain numbers and lowercase letters only because it will be part of a URL.
    4. The container name does not have to be unique, but make note of what you called it.

2. Deploy Resources Manually

    1. Set up a storage account in your Azure subscription, see: https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create
    2. Add a container in that storage account, see: https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-portal#create-a-container

### Determine Blob Authentication
You will need to choose how to authenticate to the blob storage account. This example is set up to use the "default" authentication option, which uses the [DefaultAzureCredential class](https://docs.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential) to attempt to authenticate to the blob storage backend with a list of credential types in priority order.

The instructions below use the Azure CLI to configure access to Azure storage. See https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli to get started with the Azure CLI, or use the browser accessible Azure Cloud Shell to start using the AZ CLI without installing any dependencies: https://docs.microsoft.com/en-us/azure/cloud-shell/overview

This quickstart assumes your VM in Azure has managed identity disabled, or you are not running on an Azure VM.  We will use the Azure CLI to log in to Azure and authenticate to blob storage. This only needs to be done once per user and storage account pairing. Afterwards, the user will have permissions to access any current or new blob containers in that storage account.  For the quickstart that uses managed identity instead, [use this](blob_managed_id_quickstart.md).

In a terminal on your VM:

1. To log in to Azure, run:
    ```
    az login
    ```
2. Ensure that you have assigned yourself the "Storage Blob Data Contributor" or "Storage Blob Data Owner" role for your storage account. Get the currently logged in user ID by running:
    ```
    userName=$(az ad signed-in-user show --query userPrincipalName --out tsv); echo $userName
    ```
3. Get the Azure ID of your storage account by running the following command _after_ replacing MyStorageAccountName with your storage account's name:
    ```
    storageID=$(az resource list --name MyStorageAccountName --query [*].id --out tsv); echo $storageID
    ```
A THIS POINT THINGS STOP WORKING FOR ME, I DONT SEE ANY RESULTS FROM LINE ABOVE AND IF I SPECIFY MY RG I GET AN ERROR 

4. List what roles you have assigned for your storage account by running:
    ```
    az role assignment list --assignee $userName --scope $storageID --query [*].roleDefinitionName --out tsv
    ```
5. If you do not see either the "Storage Blob Data Contributor" or "Storage Blob Data Owner" role for your storage account, add the "Storage Blob Data Owner" role by running:
    ```
    az role assignment create --assignee $userName --role 'Storage Blob Data Owner' --scope $storageID
    ```
See https://docs.microsoft.com/en-us/azure/storage/blobs/assign-azure-role-data-access for more information on assigning roles to enable access to Azure storage resources.

Next, launch GNU Radio Companion from the same terminal using:

```bash
gnuradio-companion
```

This will ensure your authentication tokens are available when running the flowgraph. 

## Run the Blob Sink Example

Open [blob-sink-example.grc](../examples/blob-sink-example.grc).

To run the flowgraph, you must:
- Change the blob_url variable to use your actual storage account URL
- Change the blob_container_name variable to use the container name you created

Run the flowgraph for a few seconds, then stop it (e.g., by closing the window that popped up).  Navigate to your blob container in the Azure portal and you should see a new blob object named "test-signal.dat".  The number of samples simulated and stored depends on how long you ran the flowgraph, but the `blob_block_length` defines the maximum (defaults to 10M samples).

## Run the Blob Source Example

Open [blob-source-example.grc](../examples/blob-source-example.grc).

To run the flowgraph, you must:
- Change the blob_url variable to use your actual storage account URL
- Change the blob_container_name variable to use the container name you created
- Change the blob_name to point to an existing blob object, which is test-signal.dat assuming you did the previous section to completion. 

Run the flowgraph and you should see the QT GUI Sink block showing the contents of your blob object, which is the signal we simulated in the previous section.

Once you are done with running the examples, delete the resources you created to ensure you do not incur ongoing charges for storage.

----


## Recommended content

### [Azure Blob storage overview](https://azure.microsoft.com/en-us/services/storage/blobs/)