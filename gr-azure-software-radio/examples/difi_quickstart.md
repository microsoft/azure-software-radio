# Quickstart: Running the DIFI source and sink block examples

The DIFI source and sink blocks are based on the IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard. They
enable users to transmit and receive digitized IF data and corresponding metadata over standard IP networks using GNU
Radio.

## Prerequisites

- Install the GNU Radio runtime, GNU Radio Companion, and the Azure Software Radio Out-of-Tree module. See the
[Azure Software Radio: Getting Started](../README.md#getting-started) section for more details.

## Run the DIFI standalone example
DIFI sink blocks have a `mode` parameter that can be set to either "Paired" or "Standalone". In standalone mode, the
user must specify values for fields that will be included in the DIFI packet stream metadata. Since the metadata values
are provided by the user, the DIFI sink can be used with any normal sample source in GNU Radio, not just sources that
generate DIFI-compliant metadata.<br>

Open the [DIFI sink standalone mode example](difi_standalone.grc) in GNU Radio Companion and run the flowgraph to see
the DIFI sink block running in standalone mode.

----
## Run the paired DIFI source and sink example
When using the DIFI sink in paired mode, the DIFI sink expects the input sample stream to include DIFI compliant
metadata in stream tags, such as those produced by the DIFI source block. If the DIFI sink does not receive the metadata
it requires, it will have unexpected behavior.

Note: To run this example, you will need to send DIFI packets to the DIFI source block in the example using an external
source, such as a DIFI compliant packet source or another flowgraph that includes a DIFI sink block.

Open the [DIFI sink paired mode example](difi_paired_example.grc) in GNU Radio Companion and run the flowgraph to see
the DIFI sink block running with a paired DIFI source block.

---
## Recommended content
### [Digital Intermediate Frequency Interoperability (DIFI) Consortium](https://dificonsortium.org/)

The organization which oversees development of the IEEE-ISTO Std 4900-2021: Digital IF Interoperability 1.0 Standard

