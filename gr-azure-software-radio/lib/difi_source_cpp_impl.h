// -*- c++ -*-
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.

#ifndef INCLUDED_AZURE_SOFTWARE_RADIO_difi_source_cpp_IMPL_H
#define INCLUDED_AZURE_SOFTWARE_RADIO_difi_source_cpp_IMPL_H

#include <azure_software_radio/difi_source_cpp.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <deque>
#include <algorithm>
#include <complex>
#include <iostream>
#include <deque>
#include <iterator>
#include <chrono>
#include <pmt/pmt.h>
#include <sys/time.h>
#include <azure_software_radio/difi_common.h>

namespace gr {
namespace azure_software_radio {

template <class T>
class difi_source_cpp_impl : public difi_source_cpp<T>
{
    double parse_vita_fixed_double(u_int64_t bits)
    {
        u_int64_t int_part = bits >> 20;
        u_int32_t frac_part = bits & 0xfffff;
        long pow = 43;
        double frac = 0;
        u_int64_t full = 0;
        while (pow > -1) {
            full += 0x1 << pow * ((int_part >> pow) & 0x1);
            pow--;
        }
        while (pow > -21) {
            u_int64_t tmp = 0x1 << abs(pow) * ((frac_part >> 20 - pow) & 0x1);
            frac += tmp == 0 ? tmp : 1 / tmp;
            pow--;
        }
        return full + frac;
    }
    struct header_data {
        u_int16_t pkt_n;
        u_int8_t type;
        u_int32_t header;
        u_int32_t stream_num;
    };

    struct context_packet {
        u_int64_t class_id;
        u_int32_t full;
        u_int64_t frac;
        u_int32_t cif;
        u_int32_t ref_point;
        double bw;
        u_int64_t if_ref_freq;
        u_int64_t rf_ref_freq;
        u_int64_t if_band_offset;
        u_int32_t ref_lvl;
        u_int32_t gain;
        double samp_rate;
        u_int64_t t_adj;
        u_int32_t t_cal;
        u_int32_t state_indicators;
        u_int64_t payload_format;
    };


private:
    template <typename  M>
    static M unpack_16(int8_t *start)
    {
      int16_t re;
      memcpy(&re, start, 2);
      int16_t imag;
      memcpy(&imag, start + 2, 2);
      return M(re, imag);
    }
    
    template <typename  M>
    static M unpack_8(int8_t *start)
    {
      int8_t re;
      memcpy(&re, start, 1);
      int8_t imag;
      memcpy(&imag, start + 1, 1);
      return M(re, imag);
    }

    void create_udp_socket();
    void create_tcp_socket();
    void reset_tcp_connection();
    typedef enum
    {
        throw_exe,
        ignore,
        warnings_forward,
        warnings_no_forward
    }context_bahavior;

    std::string d_ip_addr;
    uint32_t d_port;
    int d_stream_number;
    uint32_t d_packet_buffer_len;
    int d_socket;
    int d_client_socket;
    int d_fd_max;
    int d_packet_buffer_start_idx;
    int d_num_bytes_in_read_buffer;
    uint8_t d_socket_type;
    fd_set d_rset;
    struct timeval d_tv;
    std::vector<int8_t> d_read_buffer;
    std::vector<int8_t> d_packet_buffer;
    struct sockaddr_in d_servaddr;
    std::deque<char> d_deque;
    std::chrono::time_point<std::chrono::high_resolution_clock> last;
    long d_last_pkt_n = -1;
    pmt::pmt_t d_context;
    double d_timeout;
    u_int32_t d_last_full;
    u_int64_t d_last_frac;
    int32_t d_static_bits;
    T (*d_unpacker)(int8_t *);
    void parse_header(header_data& data);
    pmt::pmt_t make_pkt_n_dict(int pkt_n, int size_gotten);
    void unpack_context(context_packet& context);
    void unpack_context_alt(context_packet& context);
    u_int32_t d_unpack_idx_size;
    pmt::pmt_t make_context_dict(header_data& header, int size_gotten);
    int buffer_and_send(T* out, int noutput_items);
    int recv_tcp_packet();
    int d_behavior;
    bool d_send; 

public:
    difi_source_cpp_impl(std::string ip_addr,
                    uint32_t port,
                    uint8_t socket_type,
                    uint32_t stream_number,
                    uint32_t socket_buffer_size, 
                    int bit_depth,
                    int context_pkt_behavior);
    ~difi_source_cpp_impl();

    // Where all the action really happens
    int work(int noutput_items,
             gr_vector_const_void_star& input_items,
             gr_vector_void_star& output_items);
    static const uint VITA_PKT_MOD = 16;
    static const uint MS_DATA_VITA_HEADER = 0x18;
};

} // namespace azure_software_radio
} // namespace gr

#endif /* INCLUDED_AZURE_SOFTWARE_RADIO_difi_source_cpp_IMPL_H */
