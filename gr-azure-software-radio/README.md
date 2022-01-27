# Azure software radio Out of Tree Module

The Azure software radio Out of Tree (OOT) Module allows users to leverage and easily use cloud resources in GNU Radio directly within a flowgraph. This OOT module can be used in a VM in the cloud or a local machine.

## Table of Contents
- [Azure software radio Out of Tree Module](#azure-software-radio-out-of-tree-module)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installing Azure software radio OOT](#installing-azure-software-radio-oot)
    - [Running the Unit Tests](#running-the-unit-tests)
  - [Frequently Asked Questions](#frequently-asked-questions)
- [Azure software radio Out of Tree Module Blocks](#azure-software-radio-out-of-tree-module-blocks)
  - [Key Vault Block](#key-vault-block)
  - [Blob Blocks](#blob-blocks)
    - [Blob Block Descriptions](#blob-block-descriptions)
  - [Event Hub Blocks](#event-hub-blocks)
    - [Event Hub Block Descriptions](#event-hub-block-descriptions)
  - [IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard (DIFI)](#ieee-isto-std-4900-2021-digital-if-interoperability-standard-difi)
    - [DIFI Block Descriptions](#difi-block-descriptions)


## Getting Started

To get started, first please follow the install guides below.

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
This project depends on the GNU Radio 3.9.x runtime and development dependencies. This project does not
support GNU Radio 3.10.x at this time. See the [GnuRadio installation instructions](https://wiki.gnuradio.org/index.php/InstallingGR#From_Binaries) for steps on
installing GnuRadio from binaries. Some package managers do not automatically install all of the development dependencies,
so you may need to separately install and configure some of them. The Azure software radio OOT module requires the following:

```
GnuRadio 3.9.x (Note: not 3.10.x)
python 3.8 or greater
python3-pip
cmake
liborc-dev
doxygen

pytest (pip)
pybind11 (pip)
```

**NOTE:** If using the Azure CLI, you will need a recent version, (2.17.1 or newer) .This module is not compatible with
the Azure CLI availabile in the default apt repository on Ubuntu 20. If this older version of the Azure CLI is present
on your system, the installation of this OOT module may fail or the module may crash at runtime. Please install the
Azure CLI according to the recommendations found in [AZ CLI Installation in Linux](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt)


### Resolutions to Common Problems During Installation and Tests
For a list common problems and resolutions, please check our [FAQ](./docs/FAQ.md) to see if your issue has been addressed.

### Installing Azure software radio OOT

If you see error messages after running any of the following steps, stop and check our [FAQ](./docs/FAQ.md) for how to
resolve the problem.

```
git clone https://github.com/microsoft/azure-software-radio.git

cd azure-software-radio

cd gr-azure-software-radio

pip install -r python/requirements.txt

mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```

### Running the Unit Tests
Run the QA tests with any of the following methods:
 - From the terminal you'll use to run the tests, run:

    From the build directory:
    ```
    make test
    ```

    You can review detailed test ouptput (including any failures) in Testing/Temporary/LastTest.log

 - Or from the python directory:
    ```
    python -m pytest qa_*
    ```

    Pytest will show detailed test results directly in the output of this command.


## Frequently Asked Questions
For a list of common questions, including problems and resolutions, please check our [FAQ](./docs/FAQ.md)

# Azure software radio Out of Tree Module Blocks

## Key Vault Block
The Key Vault block allows users to pull down keys and secrets from an [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/general/overview) in GNU Radio.

It is expected that the user will setup and store secrets in an Azure Key Vault prior to pulling down keys using this block. To create a Key Vault, see [Create Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/secrets/quick-create-cli).

See the [Key Vault Example](./examples/README.md#key-vault-example).


## Blob Blocks
The two Blob blocks (source and sink) provide an interface to read and write samples to [Azure Blob storage](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction) in GNU Radio.

It is expected that the user will setup a storage account and a container prior to accessing Blob storage with the Blob source and sink blocks. To create a storage account, see [Create Storage Account](https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal).

### Blob Block Descriptions
 * Blob Source Block\
	The Blob source block reads samples from Azure Blob storage. This block currently supports complex64 inputs and block blobs (Page blobs and append blobs are not supported at this time).

 * Blob Sink Block\
	The Blob sink block writes samples to Azure Blob storage. This block currently supports complex64 inputs and block blobs (Page blobs and append blobs are not supported at this time).

	There are several ways to authenticate to the Azue blob backend, these blocks support authentication using a connection string, a URL with an embedded SAS token, or use credentials supported by the DefaultAzureCredential class.

	See the [Blob Examples](./examples/README.md).

## Event Hub Blocks
The Event Hub blocks (source and sink) provide an interface to send and receive events to [Azure Event Hubs](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-about) using the message passing interface in GNU Radio.

It is expected that the user will create an Event Hubs namespace, Event Hub entity and consumer group prior to using the Event Hub source and sink blocks. To create an Event Hub, see [Create an Event Hub](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-create).

### Event Hub Block Descriptions
 * EventHub Source Block\
	The EventHub source block receives a JSON formatted event message from Azure Event Hub and converts it to GNU Radio PMT format.

 * EventHub Sink Block\
	The EventHub sink block converts a PMT message to JSON and sends it to Azure Event Hub.

	These blocks support multiple ways to authenticate to the Azue Event Hub backend, such as using a connection string, a SAS token, or use credentials supported by the DefaultAzureCredential class.

	See the [Event Hub Examples](./examples/README.md).

## IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard (DIFI)
This is a set of GNU Radio blocks based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard version 1.0.

There are two DIFI blocks (source and sink) as part of this out of tree module. The Bit Depths currently supported are 8 and 16 with support for the full range of bit depths specified in the DIFI standard coming later.

### DIFI Block Descriptions
 * DIFI Source Block\
	The DIFI source block receives UDP DIFI packets from a given IP address and port. It then forwards them to GNU Radio as a complex64 (gr_complex) or signed complex 8 (std::complex<char>).
	This block emits the following tags in the following situations:
	  pck_n tag: Emitted when a missed packet occurs, will update the upstream blocks with the current packet number to expect and the current time stamps
	  context tag: Emitted when a new DIFI context packet is received with the context packet dynamic information
	  static_change: Emitted when the static parts of the DIFI context packet changes
  DIFI Advanced:
  This tab contains more advanced settings for the DIFI block and should be used by users who know the devices and network in use.

   Context Packet Mismatch Behavior
      - Default: Throws exceptions if context packet is incorrect or non-compliant
      - Ignore Mismatches - Forward data, no warnings: Entirely ignore the context packet, only forwards data
      - Throw Warnings - Forward: Displays Warnings about context packet mismatch or non-compliant context packets, but still forward DIFI data.
      - Throw Warnings - No Forward: Displays Warnings about context packet mismatch or non-compliant context packets, but won't forward data until a correct context packet is received or one that matches the given settings

 * DIFI Sink Block\
	The DIFI sink block forwards packets to a given IP address and port number and packets the data with the given bit depth. This block operates in two modes, standalone and paired.

	Pair Mode: The block expects to be paired with a DIFI source block that sends context packets, timing information, and packet count information. The sink block forwards context packets received via tags. For data packets, it adds the correct timestamps and packet number. The data format is packeted as complex64 (gr_complex) or complex signed 8 (std::complex<char>)) samples.

	Standalone Mode: In standalone mode, it is expected the user will supply the context packet information via GRC or the constructor of the class. For now, the context packet payload data are static once specified by the user. Like paired mode, the data format to pack is, complex64 (gr_complex) or complex signed 8 (std::complex<char>)) samples.

	Scaling Mode: To help mitigate quantization error, the DIFI Sink has an optional helper feature to apply a gain & offset to the input signal. The first mode "Manual" allows a user to manually set gain & offset. In Min-Max mode the user supplies the max and min expected I & Q values and the block solves for a gain & offset based on these and the specified bit depth.

	Note: this block converts from float 32 I and Q down to the specified bit depth for I and Q, which can cause significant quantization error for small signals.

    See [DIFI Examples](./examples/README.md), [DIFI Paired](./examples/difi_paired_example.grc) and [DIFI Standalone](./examples/difi_standalone.grc) for block examples.



[^1]: [GnuRadio installation instructions](https://wiki.gnuradio.org/index.php/InstallingGR#From_Binaries)







