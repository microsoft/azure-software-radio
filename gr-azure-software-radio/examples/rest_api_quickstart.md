# Quickstart: Running the REST API example

The REST API block exposes top block parameters in GNU Radio via REST such as variables and functions to enable getting status from a running flowgraph and dynamically change settings.

The block supports the following routes:
- `/status`: returns the readable settings
- `/config`: updates the writable variables with the specified configuration values
- `/call`: executes the writable functions with the specified parameters

## Prerequisites

- Install the GNU Radio runtime, GNU Radio Companion, and the Azure Software Radio Out-of-Tree module. See the
[Azure Software Radio: Getting Started](../README.md#getting-started) section for more details.

## Run the REST API Example

Open [rest-example.grc](../examples/rest_example.grc)

The flowgraph starts a REST server in Port 8000 and sets the readable and writable/callable settings.
- Readable settings that are exposed via the REST endpoint when calling `http://<addr>:8000/status` are: `samp_rate, amplitude, freq and phase`.
- Callable functions that are exposed via the REST endpoint when calling `http://<addr>:8000/call` are: `set_amplitude, set_freq`. These functions allow to modify the signal amplitude and frequency during runtime.

Run the flowgraph and you should see the QT GUI Sink blocks showing the default amplitude and frequency values of the generated signal.

### Update settings via REST using curl

To get the status of the running example using curl run the following command:
```curl -X GET http://127.0.0.1:8000/status```

The signal amplitude and frequency can be updated as follows:
```curl -X PUT http://127.0.0.1:8000/call -H 'Content-Type: application/json' -d '{"set_amplitude":2, "set_freq":10e3}'```

Confirm the new settings by looking at the QT Sink blocks or getting the status again.


