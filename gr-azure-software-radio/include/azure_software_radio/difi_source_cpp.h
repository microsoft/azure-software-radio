// -*- c++ -*- //
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.
//

#ifndef INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SOURCE_CPP_H
#define INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SOURCE_CPP_H

#include <azure_software_radio/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace azure_software_radio {

    /*!
     * \brief
     *  A DIFI source block is based on IEEE-ISTO Std 4900-2021: Digital IF Interoperability Standard
     *  The block is not fully compliant just yet. Bit Depths supported are currently 8 and 16 with full support coming at a later date.
     *  This block will emit the following tags in the following situations:
     *  pck_n tag: Emitted when a missed packet occurs, will update the upstream blocks with the current packet number to expect and the current time stamps
     *  context tag: Emitted when a new DIFI context packet is recieved with the context packet dynamic information
     *  static_change: Emitted when the static parts of the DIFI context packet changes
     * 
     *  DIFI Advanced:
     *  This tab contains more advanced settings for the DIFI block and should be used by users who know the devices and network in use. 
     * 
     *  Context Packet Mismatch Behavior
     *    - Default: Throws exceptions if context packet is incorrect or non-compliant
     *    - Ignore Mismatches - Forward data, no warnings: Entirely ignore the context packet, only forwards data
     *    - Throw Warnings - Forward: Displays Warnings about context packet mismatch or non-compliant context packets, but still forward DIFI data. 
     *    - Throw Warnings - No Forward: Displays Warnings about context packet mismatch or non-compliant context packets, 
     *                       but won't forward data until a correct context packet is received or one that does not mismatch the given settings
     * \ingroup azure_software_radio
     *
     */
    template <class T>
    class AZURE_SOFTWARE_RADIO_API difi_source_cpp : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<difi_source_cpp<T>> sptr;
  /*!
   * \brief
   *  \param ip_addr The ip address for the socket to expect DIFI packets from
   *  \param port the port number for the socket
   *  \param socket_type The socket type (TCP or UDP)
   *  \param stream_number The DIFI (VITA) stream number to expect for this stream
   *                     If stream number is -1, the stream number will be ignored, else it will be checked
   *                     against the stream number in the DIFI (VITA) packets. If they do match, the packets will be dropped.
   *  \param bit_depth The bit depth
   *  \param context_pkt_behavior Set the behavior of handling non-compliant context packets. 
   */
    static sptr make(std::string ip_addr, uint32_t port, uint8_t socket_type, uint32_t stream_number, int bit_depth, int context_pkt_behavior);

    };
    typedef difi_source_cpp<gr_complex> difi_source_cpp_fc32;
    typedef difi_source_cpp<std::complex<char>> difi_source_cpp_sc8;

  } // namespace azure_software_radio
} // namespace gr

#endif /* INCLUDED_AZURE_SOFTWARE_RADIO_DIFI_SOURCE_CPP_H */

