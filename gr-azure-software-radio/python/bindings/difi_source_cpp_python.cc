// -*- c++ -*- //
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.
//

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <azure_software_radio/difi_source_cpp.h>
// pydoc.h is automatically generated in the build directory
#include <difi_source_cpp_pydoc.h>


template <typename T>
void bind_difi_source_cpp_template(py::module& m, const char* classname)
{

    using difi_source_cpp    = ::gr::azure_software_radio::difi_source_cpp<T>;


    py::class_<difi_source_cpp, gr::sync_block, gr::block, gr::basic_block,
        std::shared_ptr<difi_source_cpp>>(m, classname,  D(difi_source_cpp))

        .def(py::init(&difi_source_cpp::make),
           py::arg("ip_addr"),
           py::arg("port"),
           py::arg("stream_number"),
           py::arg("socket_buffer_size"),
           py::arg("bit_depth"),
            D(difi_source_cpp,make)
        );
}

void bind_difi_source_cpp(py::module& m)
{
    bind_difi_source_cpp_template<gr_complex>(m, "difi_source_cpp_fc32");
    bind_difi_source_cpp_template<std::complex<char>>(m, "difi_source_cpp_sc8");
}








