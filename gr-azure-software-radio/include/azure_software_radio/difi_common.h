// -*- c++ -*- //
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.
//

#ifndef INCLUDED_DIFI_COMMON_CPP_IMPL_H
#define INCLUDED_DIFI_COMMON_CPP_IMPL_H

#include <sys/socket.h>
#include <netinet/in.h>

namespace gr {
  namespace difi {

  static const u_int8_t DIFI_HEADER_SIZE = 28;
  static const u_int8_t VITA_PKT_MOD = 16;
  static const u_int32_t MS_DATA_VITA_HEADER = 0x18;
  static const u_int64_t PICO_CONVERSION = 1000000000000U;
  static const uint16_t CONTEXT_PACKET_OFFSETS[16] = {8, 16, 20, 28, 32, 36, 44, 52, 60, 68, 72, 76, 84, 92, 96, 100};
  static const uint16_t CONTEXT_PACKET_ALT_OFFSETS[9] = {8, 16, 20, 28, 36, 44, 52, 60, 64};
  static const u_int64_t EIGHT_BIT_SIGNED_CART_LINK_EFF = 0xa00001c700000000U;
  static const u_int64_t SIXTEEN_BIT_SIGNED_CART_LINK_EFF = 0xa00001cf00000000U;
  static const u_int32_t DATA_START_IDX = 28;
  static const u_int64_t DEFAULT_STATE_AND_EVENTS = 2685009920U;
  } // namespace difi
} // namespace gr

#endif /* INCLUDED_DIFI_COMMON_CPP_IMPL_H */

