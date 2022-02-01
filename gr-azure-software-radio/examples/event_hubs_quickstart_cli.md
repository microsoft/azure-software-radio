# Quickstart: Using Azure Event Hubs in GNU Radio

Intro text.

## Prerequisites

- bulleted list of prereqs

## First thing

## Next thing

----
## Recommended content





















# Event Hub Examples
## Event Hub Example Prerequisites
To run [eventhub_sink_example.grc](../examples/eventhub_sink_example.grc) or [eventhub_source_example.grc](../examples/eventhub-source-example.grc), you must first create an Event Hub namespace, an Event Hub, and a consumer group. To deploy these resources, either click the 'Deploy to Azure' button or follow the manual deployment instructions below:

### Deploy Resources Automatically
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fazure-software-radio%2Fdocumentation%2Fcli-updates%2Fgr-azure-software-radio%2Fexamples%2Fkey_vault_example_resources.json)

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