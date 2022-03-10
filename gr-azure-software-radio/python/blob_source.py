#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
# pylint: disable=no-member
#


import queue

import azure.core.exceptions as az_exceptions
from gnuradio import gr
import numpy as np

from azure_software_radio.blob_common import blob_container_info_is_valid, get_blob_service_client
from azure_software_radio.blob_common import shutdown_blob_service_client


class BlobSource(gr.sync_block):
    """ Read samples from an Azure Blob.

    This block has multiple ways to authenticate to the Azure blob backend. Users can directly
    specify either a connection string, a URL with an embedded SAS token, or use credentials
    supported by the DefaultAzureCredential class, such as environment variables, a
    managed identity, the az login command, etc.

    This block currently only supports complex64 inputs and has only been tested with block blobs.
    Page blobs are not supported.

    Args:
    Output Type: Data type of the sample stream
    Vector Length: Number of items per vector
    Auth Method: Determines how to authenticate to the Azure blob backend. May be one of
        "connection_string", "url_with_sas", or "default".
    Connection String: Azure storage account connection string used for
        authentication if Auth Method is "connection_string".
    URL: Storage account URL string. This is required if using "default" or
        "url_with_sas" authentication. If using "url_with_sas", the URL must include a SAS
        token to access private blobs. If using a blob in a container with public permissions, the
        SAS token is not necessary.
    Container Name: Name of the container where the blob of interest is stored.
    Blob Name: The name of the block blob to read from.
    Retry Total: Total number of Azure API retries to allow before throwing an exception. Higher
        numbers make the block more resilient to intermittent failures, lower numbers help to
        more quickly iteratively debug authentication and permissions issues.
    """
    # pylint: disable=too-many-arguments, too-many-instance-attributes, arguments-differ, abstract-method
    def __init__(self, np_dtype: np.dtype, vlen: int = 1, authentication_method: str = "default",
                 connection_str: str = None, url: str = None, container_name: str = None, blob_name: str = None,
                 queue_size: int = 4, retry_total: int = 10, repeat: bool = False):
        """ Initialize the blob_source block

        Args:
            np_dtype (np.dtype): Numpy data type of each item in the stream
            vlen (int): Number of items per vector
            authentication_method (str): See "Auth Method" in class docstring above
            connection_str (optional, str): See "Connection String" in class docstring above
            url (optional, str): See "URL" in class docstring above
            container_name (str): See "Container Name" in class docstring above
            blob_name (str): See "Blob Name" in class docstring above
            queue_size (int, optional): Defaults to 4. How many blocks of data to
                buffer up before blocking. Larger numbers require more memory overhead
            retry_total (int, optional): Total number of Azure API retries to allow before throwing
                an exception
            repeat (bool): To repeat the file or not.  Currently does not cache locally so repeating
                will cause additional traffic.
        """
        # work-around the following deprecation in numpy:
        # FutureWarning: Passing (type, 1) or '1type' as a synonym of type is deprecated
        if vlen == 1:
            out_sig = [np_dtype]
        else:
            out_sig = [(np_dtype, vlen)]

        gr.sync_block.__init__(self,
                               name="blob_source",
                               in_sig=None,
                               out_sig=out_sig)

        self.queue = queue.Queue(maxsize=queue_size)
        self.buf = np.zeros((0, ), dtype=np.byte)
        self.num_buf_bytes_read = 0
        self.repeat = repeat

        self.blob_service_client = get_blob_service_client(
            authentication_method=authentication_method,
            connection_str=connection_str,
            url=url,
            retry_total=retry_total
        )

        self.blob_client = self.blob_service_client.get_blob_client(container=container_name,
                                                                    blob=blob_name)

        self.blob_iter = None

        self.blob_complete = False

        self.item_size = np_dtype().itemsize*vlen
        self.chunk_residue = b''

        self.first_run = True

        self.log = gr.logger("log_debug")

    def setup_blob_iterator(self):
        ''' get an iterator into the blob object so we can start doing a streaming download
        '''
        blob_stream = self.blob_client.download_blob(max_concurrency=1)
        blob_iter = blob_stream.chunks()

        return blob_iter

    def blob_auth_and_container_info_is_valid(self):
        ''' Run checks on authentication and the blob container before first use
        '''
        blob_container_info_is_valid(
            blob_service_client=self.blob_service_client,
            container_name=self.blob_client.container_name)

        if not self.blob_client.exists():
            container_name = self.blob_client.container_name
            blob_name = self.blob_client.blob_name
            err = az_exceptions.ResourceNotFoundError(
                f"Blob name '{blob_name} does not exist in container '{container_name}'")
            self.log.error(f"{err}")
            raise err

        return True

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
        num_data_items = int(np.floor(len(chunk)/self.item_size))

        data = np.frombuffer(buffer=chunk, count=num_data_items*self.item_size, dtype=np.byte)
        chunk_residue = chunk[num_data_items*self.item_size:]

        return data, chunk_residue

    def download_chunk_to_queue(self):
        # pylint: disable=fixme
        """
        Pull chunks from the blob, convert the bytes into a numpy array, and add to queue
        """
        # TODO: put this into a separate thread, see ADO #5897
        while not self.queue.full() and not self.blob_complete:
            try:
                chunk = next(self.blob_iter)
                self.log.debug(f"Retrieved {len(chunk)} bytes of data from blob storage")
                data, self.chunk_residue = self.chunk_to_array(
                    chunk, self.chunk_residue)
                if len(data) > 0:
                    self.queue.put(data)
            except StopIteration:
                self.log.debug("Reached the end of the blob")
                self.blob_complete = True

    def work(self, _, output_items):
        # pylint: disable=fixme
        """ Stream items from blob storage.

        Stream items out from an internal buffer. Once the internal buffer is exhausted,
        pull more data in from blob storage.

        Args:
            input_items (list of numpy arrays): Not used
            output_items (list of numpy arrays): Stream of samples to output

        Returns:
            int: Number of items generated in this work call
        """

        # connect to the blob service the first time we run
        if self.first_run:
            self.blob_auth_and_container_info_is_valid()
            self.blob_iter = self.setup_blob_iterator()
            self.first_run = False

        # get a view into the output buffer as a 1D array of bytes, so our code can copy over the data
        # without caring about the actual datatype or vlen in use
        out_view = output_items[0].view()
        out_view.shape = (output_items[0].size,)
        out = out_view.view(dtype=np.byte)

        noutput_items = len(output_items[0])

        num_remaining_bytes = len(self.buf) - self.num_buf_bytes_read

        # check if we're done
        if self.queue.empty() and num_remaining_bytes == 0 and self.blob_complete:
            if self.repeat:
                self.blob_iter = self.setup_blob_iterator()
                self.num_buf_bytes_read = 0
                self.buf = np.zeros((0, ), dtype=np.byte)
                self.blob_complete = False
                return 0 # will cause work function to start over
            shutdown_blob_service_client(self.blob_service_client)
            return -1

        # do we have anything to produce?
        nitems_produced = min(int(num_remaining_bytes/self.item_size), noutput_items)
        num_bytes_produced = nitems_produced*self.item_size
        if nitems_produced > 0:

            start_ind = self.num_buf_bytes_read
            stop_ind = self.num_buf_bytes_read+num_bytes_produced

            out[:num_bytes_produced] = self.buf[start_ind:stop_ind]
            self.num_buf_bytes_read = self.num_buf_bytes_read + num_bytes_produced

        # is it time to get more data from the queue?
        if len(self.buf) <= self.num_buf_bytes_read:
            # check for more chunks in the downloader
            # TODO: Multithread this so downloads don't block the work thread, see ADO#5897

            # don't try to download from a blob that's complete or we'll get stuck waiting on
            # api call timeouts during shutdown
            if not self.blob_complete:
                self.download_chunk_to_queue()

            # if there's data to read, go get it
            if not self.queue.empty():
                self.buf = self.queue.get()
                self.num_buf_bytes_read = 0

        return nitems_produced

    def stop(self):
        """ Cleanly shut down everything
        """

        self.blob_complete = True
        shutdown_blob_service_client(self.blob_service_client)

        return True
