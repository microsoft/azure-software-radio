# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
# pylint: disable=C0301, C0103, C0115
#

import socket
import time
import matplotlib.pyplot as plt
import numpy as np
from gnuradio import analog, blocks, gr
import azure_software_radio

# Params
samples_per_packet = 4000  # relates to MTU size
num_packets = 100

# Set up sockets
sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_rx.bind(("127.0.0.1", 3333))

sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_tx.connect(("127.0.0.1", 3334))
print("Sockets connected")

# DIFI Sink (transmit side) Flowgraph
class DifiSinkFlowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        samp_rate = 1e5  # mainly just impacts throttle, if there are warnings before the TX portion then this number is too high
        self.difi_sink = azure_software_radio.difi_sink_cpp_fc32(0, 0, '127.0.0.1', 3333, bool(
            False), samples_per_packet, 0, int(352), int(samp_rate), int(0), 0, 1000, int(72), int(8), int(2), 127, 0, 1.0, -1.0)
        self.sig_source = analog.sig_source_c(samp_rate, analog.GR_SIN_WAVE, 1000, 0.5, 0, 0)
        self.throttle = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate, True)
        self.connect(self.sig_source, self.throttle)
        self.connect(self.throttle, self.difi_sink)

tb = DifiSinkFlowgraph()

# Generate and save a bunch of DIFI packets, we start the flowgraph then start recv()'ing
msgs = []
print("Starting recv")
tb.start()
time.sleep(0.1)  # give time for DIFI Sink to start up
samples_recorded = 0
for i in range(num_packets):
    msg = sock_rx.recv(4096)  # "For best match with hardware and network realities, the value of bufsize should be a relatively small power of 2, for example, 4096"
    samples_recorded += (len(msg) - 28)/2  # pretty sure the DIFI packet always has the same overhead bytes
    msgs.append(msg)
tb.stop()
tb.wait()
sock_rx.close()

print("Switching to tx")

# DIFI Source (receive side) flowgraph
class DifiSourceFlowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)
        self.azure_software_radio_difi_source_cpp_0 = azure_software_radio.difi_source_cpp_fc32(
            '127.0.0.1', 3334, 0, 8, 0)
        self.connect(self.azure_software_radio_difi_source_cpp_0,
                     self.null_sink)

rates = []
percents = []
for trial in range(20):  # monte carlo style
    threshold = 50  # [percent]
    lowest_working_delay = 10000  # should represent the slowest anything will ever run at
    highest_failing_delay = 1  # fastest anything will run at
    for i in range(10):  # hones in on the pass/fail sweet spot
        delay = int((lowest_working_delay - highest_failing_delay)/2)
        # help add some variations between monte carlo runs
        delay += int(np.random.uniform(-100, 100))
        tb = DifiSourceFlowgraph()

        # Send DIFI packets
        print("Starting send, delay =", delay)
        tb.start()  # At this point the flowgraph is running in C++ in the background (the python below is feeding packets but its not going to slow it down)
        start_t = time.time()
        num_repeats = 40  # manually tweaked this number to give a tight curve while as low as possible
        for ii in range(num_repeats):
            for msg in msgs:
                sock_tx.send(msg)
                # time.sleep() can only go down to 1ms, need to use another method to cause a tiny delay
                k = 0
                for j in range(delay):
                    k += 1  # arbitrary processing that takes a small amount of time
        time_elapsed = time.time() - start_t

        samples_out = tb.azure_software_radio_difi_source_cpp_0.nitems_written(0)
        rate = samples_recorded*num_repeats/time_elapsed
        rates.append(rate)
        percent = samples_out/(samples_recorded*num_repeats)*100
        percents.append(percent)
        print('Received ' + str(percent) +
              '% of samples sent at a sample rate of ' + str(rate/1e6) + " MHz")

        if percent > threshold:
            lowest_working_delay = delay
        else:
            highest_failing_delay = delay

        tb.stop()
        tb.wait()
        del tb  # else there are socket issues

rates = np.asarray(rates)
plt.plot(rates/1e6, percents, '.')
plt.xlabel("Sample Rate [MHz]")
plt.ylabel("Samples Received [%]")
plt.show()
