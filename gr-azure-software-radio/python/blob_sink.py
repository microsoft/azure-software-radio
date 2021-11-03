#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

import queue
import uuid
import numpy as np
from gnuradio import gr
from azure_software_radio.blob_common import get_blob_service_client

class BlobSink(gr.sync_block):
    """ Write samples out to an Azure Blob.

    This block has multiple ways to authenticate to the Azure blob backend. Users can directly
    specify either a connection string, a URL with an embedded SAS token, or use credentials
    supported by the DefaultAzureCredential class, such as environment variables, a
    managed identity, the az login command, etc.

    This block currently only supports complex64 inputs and only supports block blobs. Page blobs
    and append blobs are not supported.

    Args:
    Auth Method: Determines how to authenticate to the Azue blob backend. May be one of
        "connection_string", "url_with_sas", or "default".
    Connection String: Azure storage account connection string used for
        authentication if Auth Method is "connection_string".
    URL Storage account URL string. This is required if using "default" or
        "url_with_sas" authentication. If using "url_with_sas", the URL must include a SAS
        token.
    Container Name: Container name to store the blob in. This container must be
        created in Azure before trying to store a blob in it.
    Blob Name: The name of the block blob to create.
    Blob Block Length: How many items to write out at once to a block in the blob. Note that
        block sizes where block_len*itemsize is greater than 4MiB will enable the use of
        high throughput block transfers. Must be an integer number of items.
    """
    # pylint: disable=too-many-arguments, too-many-instance-attributes, arguments-differ, abstract-method
    def __init__(self, authentication_method: str = "default", connection_str: str = None,
                 url: str = None, container_name: str = None, blob_name: str = None,
                 block_len: int = 500000, queue_size: int = 4):
        # pylint: disable=no-member
        """ Initialize the blob_sink block

        Args:
            authentication_method (str): See "Auth Method" in class docstring above
            connection_str (optional, str): See "Connection String" in class docstring above
            url (optional, str): See "URL" in class docstring above
            container_name (str): See "Container Name" in class docstring above
            blob_name (str): See "Blob Name" in class docstring above
            block_len (int): See "Blob Block Length" in class docstring above
            queue_size (int, optional): Defaults to 4. How many blocks of data to
                buffer up before blocking. Larger numbers require more memory overhead
        """
        gr.sync_block.__init__(self,
                               name="blob_sink",
                               in_sig=[np.complex64],
                               out_sig=[])

        self.block_len = block_len


        self.blob_service_client = get_blob_service_client(
            authentication_method=authentication_method,
            connection_str=connection_str,
            url=url
        )

        self.que = queue.Queue(maxsize=queue_size)
        self.buf = np.zeros((self.block_len, ), dtype=np.complex64)
        self.num_buf_items = 0

        self.blob_client = self.blob_service_client.get_blob_client(container=container_name,
                                                                    blob=blob_name)

        self.block_id_list = []

        self.blocks_per_commit = 2

        self.log = gr.logger("log_debug")

    def upload_queue_contents(self):
        # pylint: disable=fixme
        """
        Pull all items out of the upload queue and stage each queue item as a block in the
        current blob
        """
        # TODO: put this into a separate thread, see ADO #5897
        while not self.que.empty():

            data = self.que.get()
            data_len = len(data)*np.dtype(np.complex64).itemsize

            # TODO: Use structured logging
            self.log.debug(f"Beginning upload of {data_len} bytes")

            block_id = str(uuid.uuid4())
            self.blob_client.stage_block(block_id=block_id,
                                         data=data.tobytes(),
                                         length=data_len)

            # track block IDs so we can commit the list later
            self.block_id_list.append(block_id)

            # TODO: Use structured logging, see ADO#7767
            self.log.debug("Upload complete")

    def work(self, input_items, _):
        # pylint: disable=fixme
        """ Buffer up items for upload to blob storage.

        Buffer up items in self.block_len sized chunks. When the buffer is full, pass it over
        to an upload queue. Currently this function performs the upload in the same thread.

        Args:
            input_items (list of numpy arrays): Sample stream to process, currently 1xN items.
            output_items (list of numpy arrays): Not used

        Returns:
            int: Number of items consumed in this work call
        """

        in0 = input_items[0]

        # figure out how many items we're going to copy into the temp item buffer this
        # work call
        num_copy_items = min([self.block_len-self.num_buf_items,
                              len(in0)])

        self.buf[self.num_buf_items:self.num_buf_items +
                 num_copy_items] = in0[:num_copy_items]
        self.num_buf_items = self.num_buf_items + num_copy_items

        if self.num_buf_items == self.block_len:
            try:
                self.que.put(self.buf, block=False)

                # get fresh memory for the buffer so we don't corrupt the data we've put into the
                # upload queue
                self.buf = np.zeros((self.block_len, ), dtype=np.complex64)
                self.num_buf_items = 0
            except queue.Full:
                self.log.debug(
                    "The upload queue is full, will try to requeue in the next work call")

            # TODO: Make this step multithreaded so uploads don't block the work call, see ADO #5897
            self.upload_queue_contents()

        return num_copy_items

    def stop(self):
        """ Cleanly shut down everything
        """
        self.log.info(
            "Uploading the remaining items in the buffer and shutting down")

        if self.num_buf_items > 0:
            self.que.put(self.buf[:self.num_buf_items], block=True)
        self.upload_queue_contents()

        self.log.debug(f"Commiting {len(self.block_id_list)} block IDs")
        self.blob_client.commit_block_list(block_list=self.block_id_list)
        self.blob_service_client.close()

        return True
