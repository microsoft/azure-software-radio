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
import uuid
import json

import azure.core.exceptions as az_exceptions
from gnuradio import gr
import numpy as np
import urllib3.exceptions

from azure_software_radio.blob_common import blob_container_info_is_valid, get_blob_service_client
from azure_software_radio.blob_common import shutdown_blob_service_client


class BlobSink(gr.sync_block):
    """ Write samples out to an Azure Blob.  Use a Head block to limit the number of samples stored in the file.

    This block has multiple ways to authenticate to the Azure blob backend. Users can directly
    specify either a connection string, a URL with an embedded SAS token, or use credentials
    supported by the DefaultAzureCredential class, such as environment variables, a
    managed identity, the az login command, etc.

    For saving a SigMF recording, set the SigMF param to True and leave off the file extension
    (.sigmf-data and .sigmf-meta will be automatically added).

    Args:
    Input Type: Data type of the sample stream
    Vector Length: Number of items per vector
    Auth Method: Determines how to authenticate to the Azure blob backend. May be one of
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
    Retry Total: Total number of Azure API retries to allow before throwing an exception. Higher
        numbers make the block more resilient to intermittent failures, lower numbers help to
        more quickly iteratively debug authentication and permissions issues.
    SigMF Recording: If True, two files will be created, blobname.sigmf-data and blobname.sigmf-meta.
        The blobname.sigmf-data will contain the signal, while the blobname.sigmf-meta will contain
        metadata about the signal, provided as additional block params.
    """
    # pylint: disable=too-many-arguments, too-many-instance-attributes, arguments-differ, abstract-method
    def __init__(self, np_dtype: np.dtype, vlen: int = 1, authentication_method: str = "default",
                 connection_str: str = None, url: str = None, container_name: str = None, blob_name: str = None,
                 block_len: int = 500000, queue_size: int = 4, retry_total: int = 10, sigmf: bool = False,
                 sample_rate: float = 0, center_freq: float = np.nan, author: str = '', description: str = '',
                 hw_info: str = ''):
        """ Initialize the blob_sink block
        """
        # work-around the following deprecation in numpy:
        # FutureWarning: Passing (type, 1) or '1type' as a synonym of type is deprecated
        if vlen == 1:
            in_sig = [np_dtype]
        else:
            in_sig = [(np_dtype, vlen)]

        gr.sync_block.__init__(self,
                               name="blob_sink",
                               in_sig=in_sig,
                               out_sig=[])

        self.blob_service_client = get_blob_service_client(
            authentication_method=authentication_method,
            connection_str=connection_str,
            url=url,
            retry_total=retry_total
        )

        self.item_size = np_dtype().itemsize*vlen
        self.block_len = block_len
        self.queue = queue.Queue(maxsize=queue_size)
        self.buf = np.zeros((self.block_len*self.item_size, ), dtype=np.byte)
        self.num_buf_bytes = 0
        self.log = gr.logger(f"gr_log.{self.symbol_name()}")

        # If user accidently left .sigmf-data or meta file extension, strip it off
        if sigmf and '.sigmf' in blob_name:
            blob_name = blob_name.rsplit('.', 1)[0]

        if sigmf:
            meta_blob_client = self.blob_service_client.get_blob_client(container=container_name,
                                                                        blob=blob_name + '.sigmf-meta')
            if np_dtype == np.complex64:
                datatype_str = 'cf32_le'
            elif np_dtype == np.float32:
                datatype_str = 'rf32_le'
            elif np_dtype == np.int32: # TODO: Check that our original usage of np.int32 makes sense
                datatype_str = 'ci16_le'
            elif np_dtype == np.int16:
                datatype_str = 'ri16_le'
            elif np_dtype == np.ubyte:
                datatype_str = 'ru8'
            else:
                raise ValueError

            meta_dict = {
                "global": {
                    "core:datatype": datatype_str,
                    "core:sample_rate": float(sample_rate),
                    "core:version": "1.0.0"  # update me if the time comes
                },
                "captures": [
                    {
                        "core:sample_start": 0,
                    }
                ],
                "annotations": []
            }
            if center_freq is not np.nan:
                meta_dict["captures"][0]["core:frequency"] = float(center_freq)
            if hw_info:
                meta_dict["global"]["core:hw"] = str(hw_info)
            if author:
                meta_dict["global"]["core:author"] = str(author)
            if description:
                meta_dict["global"]["core:description"] = str(description)

            meta_blob_client.upload_blob(json.dumps(meta_dict, indent=2), overwrite=True)
            meta_blob_client.close()
            self.log.info("Meta file upload complete")
            blob_name = blob_name + '.sigmf-data'

        self.blob_client = self.blob_service_client.get_blob_client(container=container_name,
                                                                    blob=blob_name)

        self.block_id_list = []

        self.first_run = True
        self.blob_is_valid = False

    def stage_block(self, data: np.array):
        # pylint: disable=fixme
        """ Stage a block to blob storage and generate a UUID to use as a block ID
        """
        # TODO: Use structured logging, see ADO#7767
        self.log.debug(f"Beginning upload of {len(data)} bytes")

        block_id = str(uuid.uuid4())
        self.blob_client.stage_block(block_id=block_id,
                                     data=data.tobytes(),
                                     length=len(data))

        return block_id

    def upload_queue_contents(self):
        # pylint: disable=fixme
        """
        Pull all items out of the upload queue and stage each queue item as a block in the
        current blob
        """
        # TODO: put this into a separate thread, see ADO #5897
        while not self.queue.empty():

            data = self.queue.get()

            block_id = self.stage_block(data)

            # track block IDs so we can commit the list later
            self.block_id_list.append(block_id)

            # TODO: Use structured logging, see ADO#7767
            self.log.debug("Upload complete")

    def create_blob(self):
        """
        Explicitly create the blob so we can catch errors
        """
        try:
            self.blob_client.commit_block_list(block_list=[])
        except (az_exceptions.HttpResponseError, urllib3.exceptions.LocationParseError) as err:
            self.log.error("Blob sink failed when attempting to create the blob file")
            self.log.error(f"{err}")
            raise err

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

        # connect to the blob service the first time we run
        if self.first_run:
            self.blob_is_valid = blob_container_info_is_valid(
                blob_service_client=self.blob_service_client,
                container_name=self.blob_client.container_name)

            self.create_blob()

            self.first_run = False

        # get a view into the input buffer as a 1D array of bytes, so our code can copy over the data
        # without caring about the actual datatype or vlen in use
        in0 = input_items[0].reshape((input_items[0].size,)).view(dtype=np.byte)

        # figure out how many bytes we're going to copy into the temp item buffer this
        # work call
        num_copy_bytes = min([self.block_len*self.item_size-self.num_buf_bytes,
                              len(in0)])

        self.buf[self.num_buf_bytes:self.num_buf_bytes + num_copy_bytes] = in0[:num_copy_bytes]
        self.num_buf_bytes = self.num_buf_bytes + num_copy_bytes

        if self.num_buf_bytes == self.block_len*self.item_size:
            try:
                self.queue.put(self.buf, block=False)

                # get fresh memory for the buffer so we don't corrupt the data we've put into the
                # upload queue
                self.buf = np.zeros((self.block_len*self.item_size, ), dtype=np.byte)
                self.num_buf_bytes = 0
            except queue.Full:
                self.log.debug(
                    "The upload queue is full, will try to requeue in the next work call")

            # TODO: Make this step multithreaded so uploads don't block the work call, see ADO #5897
            self.upload_queue_contents()

        return int(num_copy_bytes/self.item_size)

    def stop(self):
        """ Cleanly shut down everything
        """

        if self.blob_is_valid:
            self.log.info("Uploading the remaining items in the buffer and shutting down")

            if self.num_buf_bytes > 0:
                self.queue.put(self.buf[:self.num_buf_bytes], block=True)
            self.upload_queue_contents()

            self.log.debug("Commiting {} block IDs".format(len(self.block_id_list)))

            self.blob_client.commit_block_list(block_list=self.block_id_list)

        shutdown_blob_service_client(self.blob_service_client)

        return True
