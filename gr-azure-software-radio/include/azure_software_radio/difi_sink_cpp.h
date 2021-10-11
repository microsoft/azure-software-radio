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

    /*!
     * \brief 
     *  A DIFI sink block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard
     *  The block is not fully compliant just yet. Bit Depths supported are currently 8 and 16 with full support coming at a later date.
     *  Note, this block will causes quantization error if using with gr_complex since it will convert from float 32 I and Q to the bit_depth I and Q
     * 
     * \ingroup azure_software_radio
     *
     */
    template <class T>
    class AZURE_SOFTWARE_RADIO_API difi_sink_cpp : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<difi_sink_cpp<T>> sptr;
      /*!

        \param reference_time_full The initial refernce time full for the DIFI (VITA) data packets until a timing tag is recieved via pkt_n tag
                                   or a context packet tag. The time reference will never be updated if in standalone mode
        \param reference_time_frac The initial refernce time frac for the DIFI (VITA) data packets until a timing tag is recieved via pkt_n tag
                                   or a context packet tag. The time reference will never be updated if in standalone mode
        \param ip_addr The ip address for the socket that DIFI (VITA) packets will be forwared to
        \param port the port number for the socket on the host that the DIFI (VITA) packets will be forwared to
        \param mode Either standalone or paired. Paired mode is expected to have a DIFI (VITA) source block upstream in the flowgraph, standalone expects no such block, but context packet information must be given
        \param samples_per_packet The number of samples for DIFI (VITA) data packet (header included) that this block with send out via the udp socket (Cannot exceed the MTU size in bytes)
        \param stream_number The DIFI (VITA) stream number to expect for this stream.
        \param reference_point The Reference point for the stream, either ADC or DAC (only used if the context packet size is 108)
        \param samp_rate the sample rate
        \param packet_class The packet class of either 0, 1, or 2 (See 2.2.2 Standard Flow Signal Context Packet of the DIFI spec for details).
        \param oui The orginizational unique identfier. 
        \param context_interval the number of data packets to send before sending the next context packet
        \param context_pack_size The size of the context packet, either 72 or 108 (Which are supported by MS Spec)
        \param bit_depth The bit depth
        
       */
      static sptr make(u_int32_t reference_time_full, u_int64_t reference_time_frac, std::string ip_addr, uint32_t port, bool mode, uint32_t samples_per_packet, 
                      int stream_number, int reference_point, u_int64_t samp_rate, int packet_class, int oui, int context_interval, int context_pack_size, int bit_depth);
    };
    typedef difi_sink_cpp<gr_complex> difi_sink_cpp_fc32;
    typedef difi_sink_cpp<std::complex<char>> difi_sink_cpp_sc8;
  } // namespace azure_software_radio
} // namespace gr

#endif /* INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SINK_CPP_H */

