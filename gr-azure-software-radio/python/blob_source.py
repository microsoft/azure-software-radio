#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#


import numpy as np
from gnuradio import gr
import queue

from azure_software_radio.blob_common import get_blob_service_client, shutdown_blob_service_client


class blob_source(gr.sync_block):
    """ Read samples from an Azure Blob.

    This block has multiple ways to authenticate to the Azure blob backend. Users can directly
    specify either a connection string, a URL with an embedded SAS token, or use credentials
    supported by the DefaultAzureCredential class, such as environment variables, a
    managed identity, the az login command, etc.

    This block currently only supports complex64 inputs and has only been tested with block blobs.
    Page blobs are not supported.

    Args:
    Auth Method: Determines how to authenticate to the Azue blob backend. May be one of
        "connection_string", "url_with_sas", or "default".
    Connection String: Azure storage account connection string used for
        authentication if Auth Method is "connection_string".
    URL: Storage account URL string. This is required if using "default" or
        "url_with_sas" authentication. If using "url_with_sas", the URL must include a SAS
        token.
    Container Name: Name of the container where the blob of interest is stored.
    Blob Name: The name of the block blob to read from.
    """

    def __init__(self, authentication_method: str = "default", connection_str: str = None,
                 url: str = None, container_name: str = None, blob_name: str = None,
                 queue_size: int = 4):
        """ Initialize the blob_source block

        Args:
            authentication_method (str): See "Auth Method" in class docstring above
            connection_str (optional, str): See "Connection String" in class docstring above
            url (optional, str): See "URL" in class docstring above
            container_name (str): See "Container Name" in class docstring above
            blob_name (str): See "Blob Name" in class docstring above
            queue_size (int, optional): Defaults to 4. How many blocks of data to
                buffer up before blocking. Larger numbers require more memory overhead
        """
        gr.sync_block.__init__(self,
                               name="blob_source",
                               in_sig=None,
                               out_sig=[np.complex64])

        self.q = queue.Queue(maxsize=queue_size)
        self.buf = np.zeros((0, ), dtype=np.complex64)
        self.num_buf_items_read = 0

        self.blob_service_client = get_blob_service_client(
            authentication_method=authentication_method,
            connection_str=connection_str,
            url=url
        )

        self.blob_client = self.blob_service_client.get_blob_client(container=container_name,
                                                                    blob=blob_name)

        self.blob_stream = self.blob_client.download_blob(max_concurrency=1)
        self.blob_iter = self.blob_stream.chunks()

        self.blob_complete = False

        self.itemsize = np.complex64().itemsize
        self.chunk_residue = b''

        self.log = gr.logger("log_debug")

    def chunk_to_array(self, chunk: bytes, chunk_residue: bytes):
        """ Convert bytes into a new numpy array with an integer number of elements

        Args:
            chunk (bytes): New bytes to convert to a numpy array
            chunk_residue (bytes): leftover bytes from previous calls where the size of the chunk
               couldn't create an integer number of numpy array elements

        Returns:
            tuple(numpy array, bytes): The new numpy array and any leftover bytes from this call
        """

        chunk = chunk_residue + chunk
        num_data_items = int(np.floor(len(chunk)/self.itemsize))

        data = np.frombuffer(buffer=chunk, count=num_data_items, dtype=np.complex64)
        chunk_residue = chunk[num_data_items*self.itemsize:]

        return data, chunk_residue

    def download_chunk_to_queue(self):
        """
        Pull chunks from the blob, convert the bytes into a numpy array, and add to queue
        """
        # TODO: put this into a separate thread
        while not self.q.full() and not self.blob_complete:

            try:
                self.log.debug("Retrieving next block of data from blob storage")
                chunk = self.blob_iter.next()
                self.log.debug("Retrieved {} bytes of data from blob storage".format(len(chunk)))
                data, self.chunk_residue = self.chunk_to_array(chunk, self.chunk_residue)
                if len(data) > 0:
                    self.q.put(data)
            except StopIteration:
                self.log.debug("Reached the end of the blob")
                self.blob_complete = True

    def work(self, input_items, output_items):
        """ Stream items from blob storage.

        Stream items out from an internal buffer. Once the internal buffer is exhausted,
        pull more data in from blob storage.

        Args:
            input_items (list of numpy arrays): Not used
            output_items (list of numpy arrays): Stream of samples to output

        Returns:
            int: Number of items generated in this work call
        """

        out = output_items[0]
        noutput_items = len(out)

        num_remaining_items = len(self.buf) - self.num_buf_items_read

        # check if we're done
        if self.q.empty() and num_remaining_items == 0 and self.blob_complete:
            shutdown_blob_service_client(self.blob_service_client)
            return -1

        # do we have anything to produce?
        nitems_produced = min(num_remaining_items, noutput_items)

        if nitems_produced > 0:

            start_ind = self.num_buf_items_read
            stop_ind = self.num_buf_items_read+nitems_produced

            out[:nitems_produced] = self.buf[start_ind:stop_ind]
            self.num_buf_items_read = self.num_buf_items_read + nitems_produced

        # is it time to get more data from the queue?
        if len(self.buf) <= self.num_buf_items_read:
            # check for more chunks in the downloader
            # TODO: Multithread this so downloads don't block the work thread

            # don't try to download from a blob that's complete or we'll get stuck waiting on
            # api call timeouts during shutdown
            if not self.blob_complete:
                self.download_chunk_to_queue()

            # if there's data to read, go get it
            if not self.q.empty():
                self.buf = self.q.get()
                self.num_buf_items_read = 0

        return nitems_produced

    def stop(self):
        """ Cleanly shut down everything
        """

        self.blob_complete = True
        shutdown_blob_service_client(self.blob_service_client)

        return True
