// -*- c++ -*- //
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.
//

#ifndef INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SINK_CPP_H
#define INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SINK_CPP_H

#include <azure_software_radio/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace azure_software_radio {
  
    template <class T>
    class AZURE_SOFTWARE_RADIO_API difi_sink_cpp : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<difi_sink_cpp<T>> sptr;
      
      static sptr make(u_int32_t reference_time_full, u_int64_t reference_time_frac, std::string ip_addr, uint32_t port, bool mode, uint32_t samples_per_packet, 
                      int stream_number, int reference_point, u_int64_t samp_rate, int packet_class, int oui, int context_interval, int context_pack_size, int bit_depth, 
                      int scaling, float gain, gr_complex offset, float max_iq, float min_iq);
    };
    typedef difi_sink_cpp<gr_complex> difi_sink_cpp_fc32;
    typedef difi_sink_cpp<std::complex<char>> difi_sink_cpp_sc8;

  } // namespace azure_software_radio
} // namespace gr

#endif /* INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SINK_CPP_H */

