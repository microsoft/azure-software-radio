# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#

if(NOT PKG_CONFIG_FOUND)
    INCLUDE(FindPkgConfig)
endif()
PKG_CHECK_MODULES(PC_AZURE_SOFTWARE_RADIO azure_software_radio)

FIND_PATH(
    AZURE_SOFTWARE_RADIO_INCLUDE_DIRS
    NAMES azure_software_radio/api.h
    HINTS $ENV{AZURE_SOFTWARE_RADIO_DIR}/include
        ${PC_AZURE_SOFTWARE_RADIO_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    AZURE_SOFTWARE_RADIO_LIBRARIES
    NAMES gnuradio-azure_software_radio
    HINTS $ENV{AZURE_SOFTWARE_RADIO_DIR}/lib
        ${PC_AZURE_SOFTWARE_RADIO_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/azure_software_radioTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(AZURE_SOFTWARE_RADIO DEFAULT_MSG AZURE_SOFTWARE_RADIO_LIBRARIES AZURE_SOFTWARE_RADIO_INCLUDE_DIRS)
MARK_AS_ADVANCED(AZURE_SOFTWARE_RADIO_LIBRARIES AZURE_SOFTWARE_RADIO_INCLUDE_DIRS)
