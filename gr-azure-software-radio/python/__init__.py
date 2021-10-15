#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio Azure software radio module. Place your Python package
description here (python/__init__.py).
'''
import os

# constants
CONTEX_STRUCT_FORMAT = '!Q I Q I I Q Q Q Q I I Q Q I I Q'
CONTEX_ALT_PACK_STRUCT_FORMAT = '!Q I Q Q Q Q Q I Q'
CONTEX_ALT_PACK_STRUCT_FORMAT_FULL = '!I I Q I Q Q Q Q Q I Q'
CONTEX_PACK_STRUCT_FORMAT = '!I I Q I Q I I Q Q Q Q I I Q Q I I Q'
DATA_PACKET_METADATA_FORMAT = '!I I Q I Q'
DIFI_HEADER_SIZE = 28
VITA_PKT_MOD = 16
MS_DATA_VITA_HEADER = 0x18
# import pybind11 generated symbols into the azure_software_radio namespace
try:
    # this might fail if the module is python-only
    from .azure_software_radio_python import *
except ModuleNotFoundError:
    pass

# import any pure python here
from .blob_sink import blob_sink
from .blob_source import blob_source
from . import blob_common
