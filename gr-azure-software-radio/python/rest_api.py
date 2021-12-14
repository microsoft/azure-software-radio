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
import uvicorn
from fastapi import FastAPI
from gnuradio import gr


class RestApi(gr.basic_block):

    """ Initialize the rest_api block

        Args:
            tbself: This is a reference to the topblock self. This gives the rest_api block
                    access to the variables & callbacks of the topblock.
            port: The desired server listening port.

    """
    def __init__(self, tbself, port):
        gr.basic_block.__init__(self,
                                name="rest_api",
                                in_sig=[],
                                out_sig=[])
        app = FastAPI()
        @app.get("/get-locals")
        def get_locals():
            return dir(tbself)

        @app.get("/get-by-name")
        def get_by_name(name):
            value = getattr(tbself, name)
            return {name : value}

        @app.put("/set-by-name")
        def set_by_name(set_dict: dict):
            for name in set_dict:
                if name not in dir(tbself):
                    return {"Error": "Var not found"}
                try:
                    setattr(tbself, name, set_dict[name])
                except Exception:
                    return {"Error": f"could not set {name}"}
            return {"All" : "set"}

        @app.put("/call-by-name")
        def call_by_name(set_dict: dict):
            for name in set_dict:
                if name not in dir(tbself):
                    return {"Error": f"Func: {name} not found"}
                try:
                    func = getattr(tbself, name)
                    func(set_dict[name])
                except Exception:
                    return {'Error':f'Could not set {name}'}
            return {"Ran":"ok"}

        self.server_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={'port':port}, daemon=True)
        self.server_thread.start()
