// -*- c++ -*- //
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.
//


#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <azure_software_radio/difi_sink_cpp.h>
// pydoc.h is automatically generated in the build directory
#include <difi_sink_cpp_pydoc.h>

template <typename T>
void bind_difi_sink_cpp_template(py::module& m, const char* classname)
{

    using difi_sink_cpp    = ::gr::azure_software_radio::difi_sink_cpp<T>;


    py::class_<difi_sink_cpp, gr::sync_block, gr::block, gr::basic_block,
        std::shared_ptr<difi_sink_cpp>>(m, classname, D(difi_sink_cpp))

        .def(py::init(&difi_sink_cpp::make),
           py::arg("reference_time_full"),
           py::arg("reference_time_frac"),
           py::arg("ip_addr"),
           py::arg("port"),
           py::arg("mode"),
           py::arg("samples_per_packet"),
           py::arg("stream_number"),
           py::arg("reference_point"),
           py::arg("samp_rate"),
           py::arg("packet_class"),
           py::arg("oui"),
           py::arg("context_interval"),
           py::arg("context_pack_size"),
           py::arg("bit_depth"),
           py::arg("scaling"),
           py::arg("gain"),
           py::arg("offset"),
           py::arg("max_iq"),
           py::arg("min_iq"),
           D(difi_sink_cpp,make)
        );

}

void bind_difi_sink_cpp(py::module& m)
{
    bind_difi_sink_cpp_template<gr_complex>(m, "difi_sink_cpp_fc32");
    bind_difi_sink_cpp_template<std::complex<char>>(m, "difi_sink_cpp_sc8");
}








