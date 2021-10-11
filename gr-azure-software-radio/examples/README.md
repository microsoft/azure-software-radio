- [DIFI Examples](#difi-examples)
- [Key Vault Example](#key-vault-example)

# DIFI Examples

The DIFI Source block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard. The example shows the use of the block in both paired and standalone mode. In paired mode, the DIFI sink is expected to be paired with a DIFI source block, else it will have unexpected behavior. If no DIFI source block is used, the DIFI sink block should be used in standalone mode. In standalone mode one must specify the fields that would have been in a context packet in paired mode. The examples show both of these situations.

# Key Vault Example

The Key Vault block pulls given keys from a Azure Key Vault given the vault name. If a list element is a string, that string is the key that will be pulled and the key is also the name of the variable set in GRC. If a list element is a tuple, the first item of the tuple is the key that will be pulled and the second element is the name of variable in GRC.

In the example, you can see the correct way to input values into the Azure Key Vault block, both tuple and no tuple (renaming). 

To run the flowgraph correctly, you must setup a Key Vault resource in Azure and replace the KeyVault Name with your Key Vault resource name. 

Also, the example assume you have seed, secretscramble, and mysecretstring keys in your Key Vault. See https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli to get started with Key Vault


When your resources are ready in Azure, the flowgraph should pull the values from Azure Key Vault, and scramble the sequence with those pulled values.

If you want to enable the Azure Blob sink block, you will need to also setup a storage account and container in that account to store the data. The point of showing this is so that one can see how to use Azure Key Vault to get connection strings to use with Azure services, like Blob. 
    
