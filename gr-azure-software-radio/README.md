# Testing
To run the QA tests for the blob blocks, you must first create a storage account on Azure and 
obtain the connection string. Next, export this connection string into an environment variable named
"AZURE_STORAGE_CONNECTION_STRING". 

Also generate a SAS token for the storage account with at least read and list permissions so we can
test out all the auth options for the blob blobs. 

The blob QA code requires an environment variable named "AZURE_STORAGE_URL" containing the URL to 
the storage account, trailing '/' is optional. It also requires a AZURE_STORAGE_SAS environment
variable containing just the SAS token string for the blob storage account to test against. 

Finally, you must have at least one set of credentials supported by DefaultAzureCredential in your
environment that has permissions to the blob account to test against. Running `az login` should be
sufficient to provide this. 

The QA code will create a randomly generated container to store
unit test data requiring interactions with actual Azure infrastructure. 