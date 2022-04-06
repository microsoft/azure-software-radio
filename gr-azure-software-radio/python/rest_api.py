#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#
# pylint: disable=no-member, abstract-method, broad-except, unused-variable
#

import threading

from typing import List
from fastapi import FastAPI
from fastapi import HTTPException, status
from gnuradio import gr

import uvicorn

class RestApi(gr.basic_block):

    """ REST endpoints to configure a top block and get status information.

        The following routes are supported as part of the top block in an unauthenticated mode:
            - GET http://hostname:<port>/status
            - GET http://hostname:<port>/config
            - PUT http://hostname:<port>/config
            - PATCH http://hostname:<port>/config

        Args:
            tbself: This is a reference to the top block self. This gives the rest_api block
                    access to the variables & callbacks of the top block.
            port: The desired server listening port.
            read_settings: List of allowable read-only settings in the top block
            write_settings: List of allowable write-only settings in the top block

    """

    def __init__(self, tbself, port, read_settings: List[str] = None, write_settings: List[str] = None):
        gr.basic_block.__init__(self,
                                name="rest_api",
                                in_sig=[],
                                out_sig=[])
        app = FastAPI()

        @app.get("/status")
        def get_status():
            """
            Get the block's readable status settings
            """

            read_status = {}
            all_settings = dir(tbself)
            if read_settings:
                for name in read_settings:
                    if name in all_settings:
                        read_status[name] = getattr(tbself, name)

            return read_status

        @app.get("/config")
        def get_config():
            """
            Get the block's writeable configuration settings
            """
            all_settings = dir(tbself)
            config = {}
            if write_settings:
                for name in write_settings:
                    if name in all_settings:
                        config[name] = getattr(tbself, name)

            return config

        @app.put("/config")
        def replace_config_settings(
                settings: dict):
            """
            Replaces the block's writeable configuration settings
            """
            all_settings = dir(tbself)

            if write_settings:
                for name in settings:
                    if name not in write_settings:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST)
                    try:
                        setattr(tbself, name, settings[name])
                        return settings
                    except Exception:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED)

        self.server_thread = threading.Thread(
            target=uvicorn.run, args=(app,), kwargs={'port': port}, daemon=True)
        self.server_thread.start()
