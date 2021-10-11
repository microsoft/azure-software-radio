# Azure software radio Out of Tree Module

The Azure software radio Out of Tree (OOT) Module allows users to leverage and easily use cloud resources in GNU Radio directly within a flowgraph. This OOT module can be used in a VM in the cloud or a local machine.

- [Azure software radio Out of Tree Module](#azure-software-radio-out-of-tree-module)
	- [Key Vault Block](#key-vault-block)
	- [Blob](#blob)
		- [Blob Blocks Description](#blob-blocks-description)
	- [IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard (DIFI)](#ieee-isto-std-4900-2021-digital-if-interoperability-standard-difi)
		- [DIFI Blocks Description](#difi-blocks-description)

## Key Vault Block
The Key Vault block allows users to pull down keys and secrets from an [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/general/overview) in GNU Radio.

It is expected that the user will setup and store secrets in an Azure Key Vault prior to pulling down keys using this block. To create a Key Vault, see [Create Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli).

See the [Key Vault Example](../examples/README.md#key-vault-example).

## Blob
The two Blob blocks (source and sink) provide an interface to read and write samples to [Azure Blob storage](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction) in GNU Radio.

It is expected that the user will setup a storage account and a container prior to accessing Blob storage with the Blob source and sink blocks. To create a storage account, see [Create Storage Account](https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal). 

### Blob Blocks Description
 * Blob Source Block  
	The Blob source block reads samples from Azure Blob storage. This block currently supports complex64 inputs and block blobs (Page blobs and append blobs are not supported at this time).

 * Blob Sink Block  
	The Blob sink block writes samples to Azure Blob storage. This block currently supports complex64 inputs and block blobs (Page blobs and append blobs are not supported at this time).

	There are several ways to authenticate to the Azue blob backend, these blocks support authentication using a connection string, a URL with an embedded SAS token, or use credentials supported by the DefaultAzureCredential class.
	
	See the [Blob Examples](../examples/README.md).

## IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard (DIFI)
This is a set of GNU Radio blocks based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard version 1.0. 

There are two DIFI blocks (source and sink) as part of this out of tree module. The Bit Depths currently supported are 8 and 16 with support for the full range of bit depths specified in the DIFI standard coming later.

### DIFI Blocks Description
 * DIFI Source Block  
	The DIFI source block receives UDP DIFI packets from a given IP address and port. It then forwards them to GNU Radio as a complex64 (gr_complex) or signed complex 8 (std::complex<char>).  
	This block emits the following tags in the following situations:  
	  pck_n tag: Emitted when a missed packet occurs, will update the upstream blocks with the current packet number to expect and the current time stamps  
	  context tag: Emitted when a new DIFI context packet is received with the context packet dynamic information  
	  static_change: Emitted when the static parts of the DIFI context packet changes  
	
 * DIFI Sink Block  
	The DIFI sink block forwards packets to a given IP address and port number and packets the data with the given bit depth. This block operates in two modes, standalone and paired.
	
	Pair Mode: The block expects to be paired with a DIFI source block that sends context packets, timing information, and packet count information. The sink block forwards context packets received via tags. For data packets, it adds the correct timestamps and packet number. The data format is packeted as complex64 (gr_complex) or complex signed 8 (std::complex<char>)) samples.  

	Standalone Mode: In standalone mode, it is expected the user will supply the context packet information via GRC or the constructor of the class. For now, the context packet payload data are static once specified by the user. Like paired mode, the data format to pack is, complex64 (gr_complex) or complex signed 8 (std::complex<char>)) samples.

	Note: this block converts from float 32 I and Q down to the specified bit depth for I and Q, which can cause significant quantization error for small signals.

    See [DIFI Examples](../examples/README.md), [DIFI Paired](../examples/difi_paired_example.grc) and [DIFI Standalone](../examples/difi_standalone.grc) for block examples.




