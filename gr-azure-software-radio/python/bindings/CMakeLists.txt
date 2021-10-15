# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT azure_software_radio_sources)
    MESSAGE(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT azure_software_radio_sources)

########################################################################
# Check for pygccxml
########################################################################
GR_PYTHON_CHECK_MODULE_RAW(
    "pygccxml"
    "import pygccxml"
    PYGCCXML_FOUND
    )

include(GrPybind)

########################################################################
# Python Bindings
########################################################################

list(APPEND azure_software_radio_python_files
    difi_source_cpp_python.cc
    difi_sink_cpp_python.cc python_bindings.cc)

GR_PYBIND_MAKE_OOT(azure_software_radio 
   ../..
   gr::azure_software_radio
   "${azure_software_radio_python_files}")

install(TARGETS azure_software_radio_python DESTINATION ${GR_PYTHON_DIR}/azure_software_radio COMPONENT pythonapi)
