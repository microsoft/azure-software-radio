// -*- c++ -*-
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.

#include <gnuradio/io_signature.h>
#include "difi_sink_cpp_impl.h"
#include <arpa/inet.h>

namespace gr {
  namespace azure_software_radio {

    template <class T>
    typename difi_sink_cpp<T>::sptr
    difi_sink_cpp<T>::make(u_int32_t reference_time_full, u_int64_t reference_time_frac, std::string ip_addr, uint32_t port, uint8_t socket_type,
                          bool mode, uint32_t samples_per_packet, int stream_number, int reference_point, u_int64_t samp_rate, 
                          int packet_class, int oui, int context_interval, int context_pack_size, int bit_depth)
    {
      return gnuradio::make_block_sptr<difi_sink_cpp_impl<T>>(reference_time_full, reference_time_frac, ip_addr, port, socket_type, mode, 
                                                              samples_per_packet, stream_number, reference_point, samp_rate, packet_class, oui, context_interval, context_pack_size, bit_depth);
    }

    template <class T>
    difi_sink_cpp_impl<T>::difi_sink_cpp_impl(u_int32_t reference_time_full, u_int64_t reference_time_frac, std::string ip_addr, 
                                              uint32_t port, uint8_t socket_type, bool mode, uint32_t samples_per_packet, int stream_number, int reference_point, 
                                              u_int64_t samp_rate, int packet_class, int oui, int context_interval, int context_pack_size, int bit_depth)
      : gr::sync_block("difi_sink_cpp_impl",
              gr::io_signature::make(1, 1, sizeof(T)),
              gr::io_signature::make(0, 0, 0)), d_stream_number(int(stream_number)), d_reference_point(reference_point), d_full_samp(samp_rate), d_oui(oui), 
              d_packet_class(packet_class), d_pkt_n(0), d_current_buff_idx(0), d_pcks_since_last_reference(0), d_is_paired_mode(mode), d_packet_count(0), d_context_packet_count(0), d_context_packet_size(context_pack_size), d_contex_packet_interval(context_interval)

    {
      memset(&d_servaddr, 0, sizeof(d_servaddr));
      d_servaddr.sin_family = AF_INET;
      d_servaddr.sin_port = htons(port);
      d_servaddr.sin_addr.s_addr = inet_addr(ip_addr.c_str());
      d_socket_type = (socket_type == 1) ?  SOCK_STREAM : SOCK_DGRAM;

      d_tv.tv_sec = 0;
      d_tv.tv_usec = 10000;

      if(d_socket_type == SOCK_DGRAM)
      {
        create_udp_socket();
      }
      else
      {
        create_tcp_socket();
      }

      if (samples_per_packet < 2)
      {
        GR_LOG_ERROR(this->d_logger, "samples per packet cannot be less than 2, (to ensure one 32 bit word is filled)");
        throw std::runtime_error("samples per packet cannot be less than 2, (to ensure one 32 bit word is filled)");
      }
      d_context_key = pmt::intern("context");
      d_pkt_n_key = pmt::intern("pck_n");
      d_static_change_key = pmt::intern("static_change");
      d_full = reference_time_full;
      d_frac = reference_time_frac;
      d_static_bits = 0x18e00000; // default, will change after first packet else, this is the DIFI standard first 12 bits
      d_context_static_bits = 0x49000000;// default, will change after first packet else, this is the DIFI standard first 8 bits
      d_unpack_idx_size = bit_depth == 8 ? 1 : 2;
      d_samples_per_packet = samples_per_packet;
      d_time_adj = (double)d_samples_per_packet / samp_rate; 
      d_data_len = samples_per_packet * d_unpack_idx_size * 2;
      u_int32_t tmp_header_data = d_static_bits ^ d_pkt_n << 16 ^ (d_data_len / 4);
      u_int32_t tmp_header_context = d_context_static_bits ^ d_context_packet_count << 16 ^ (context_pack_size  / 4);
      u_int64_t class_id = d_oui << 32 ^ d_packet_class;
      d_raw.resize(difi::DIFI_HEADER_SIZE);
      pack_u32(&d_raw[0], tmp_header_data);
      pack_u32(&d_raw[4], d_stream_number);
      int idx = 0;
      pack_u64(&d_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], class_id);
      pack_u32(&d_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
      pack_u64(&d_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);

      //pack context for standalone mode only
      d_context_raw.resize(context_pack_size);
      pack_u32(&d_context_raw[0], tmp_header_context);
      pack_u32(&d_context_raw[4], d_stream_number);
      idx = 0;
      pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], class_id);
      // this is static since only 8 or 16 bit signed complex cartesian is supported for now and item packing is always link efficient
      // see 2.2.2 Standard Flow Signal Context Packet in the DIFI spec for complete information
      u_int64_t data_payload_format = bit_depth == 8 ? difi::EIGHT_BIT_SIGNED_CART_LINK_EFF : difi::SIXTEEN_BIT_SIGNED_CART_LINK_EFF;

      u_int32_t state_and_event_id =difi::DEFAULT_STATE_AND_EVENTS; // default no events or state values. See 7.1.5.17 The State and Event Indicator Field of the VITA spec
      u_int64_t to_vita_bw = u_int64_t(samp_rate * .8) << 20; // no fractional bw or samp rate supported in gnuradio, see 2.2.2 Standard Flow Signal Context Packet for bandwidth information
      u_int64_t to_vita_samp_rate = samp_rate << 20;
      if(context_pack_size == 72)// this check is a temporary work around for a non-compliant hardware device
      {
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], 966885376U);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], to_vita_bw);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], to_vita_samp_rate);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], state_and_event_id); 
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]], data_payload_format);

      }
      else
      {
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], reference_point);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], to_vita_bw);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], samp_rate);
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], 0);
        pack_u32(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], state_and_event_id); 
        pack_u64(&d_context_raw[difi::CONTEXT_PACKET_OFFSETS[idx++]], data_payload_format);
      }
      d_out_buf.resize(d_data_len);
    }

    template <class T>
    difi_sink_cpp_impl<T>::~difi_sink_cpp_impl()
    {
      close(d_socket);
      FD_CLR(d_socket,&d_fdset);
    }

    template <class T>
    int difi_sink_cpp_impl<T>::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      if(d_socket_type == SOCK_STREAM)
      {
        socklen_t addr_len = sizeof(d_servaddr);
        if(getpeername(d_socket, (struct sockaddr*)&d_servaddr, &addr_len) < 0)
        {
          close(d_socket);
          create_tcp_socket();

          if(getpeername(d_socket, (struct sockaddr*)&d_servaddr, &addr_len) < 0)
          {
            GR_LOG_DEBUG(this->d_logger, "No connection. Attempting to re-connect the socket");
            return 0;
          }
        }
        else
        {
          if(select(d_socket + 1, NULL, &d_fdset, NULL, &d_tv) < 0)
          {
            int error_code;
            socklen_t len = sizeof(error_code);
            getsockopt(d_socket, SOL_SOCKET, SO_ERROR, &error_code, &len);
            GR_LOG_ERROR(this->d_logger, "Failed to select file descriptor for socket - error code: " + std::to_string(error_code));
            throw std::runtime_error("Failed to select file descriptor for socket - error code: " + std::to_string(error_code));
          }

          if(!FD_ISSET(d_socket,&d_fdset))
          {
            return 0;
          }
        }
      }

      const T *in = reinterpret_cast<const T*>(input_items[0]);

      if(d_is_paired_mode)
      {
        process_tags(noutput_items);
      }
        
      for(int i = 0; i < noutput_items; i++)
      {
        this->pack_T(in[i]);
        d_current_buff_idx += 2 * d_unpack_idx_size;
        if(d_current_buff_idx >= d_out_buf.size())
        {
          if(!d_is_paired_mode and d_packet_count % d_contex_packet_interval == 0)
              send_context();

          auto to_send = pack_data();
          if(d_socket_type == SOCK_DGRAM and
              sendto(d_socket, &to_send[0], to_send.size(), 0, (const struct sockaddr *) &d_servaddr, sizeof(d_servaddr)) != to_send.size())
          {
            GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
            throw std::runtime_error("Send failed to send msg on socket correctly");
          }
          if(d_socket_type == SOCK_STREAM and
            send(d_socket, &to_send[0], to_send.size(), 0) != to_send.size())
          {
            GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
            throw std::runtime_error("Send failed to send msg on socket correctly");
          }

          d_pkt_n = (d_pkt_n + 1) % difi::VITA_PKT_MOD;
          d_current_buff_idx = 0;
          d_pcks_since_last_reference++;
          d_packet_count++;
        }
      }
      return noutput_items;
    }

    template <class T>
    void difi_sink_cpp_impl<T>::process_tags(int noutput_items)
    {
      auto abs_offset = this->nitems_read(0);
      std::vector<tag_t> tags;
      this->get_tags_in_range(tags, 0, abs_offset, abs_offset + noutput_items);
      for(tag_t tag : tags)
      {
        if(pmt::eqv(d_context_key, tag.key))
        {
          auto raw = pmt::dict_ref(tag.value, pmt::intern("raw"), pmt::get_PMT_NIL());;
          std::vector<int8_t> to_send = pmt::s8vector_elements(raw);
          d_raw = to_send;
          if(d_socket_type == SOCK_DGRAM and
              sendto(d_socket, &to_send[0], to_send.size(), 0, (const struct sockaddr *) &d_servaddr, sizeof(d_servaddr)) != to_send.size())
          {
            GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
            throw std::runtime_error("Send failed to send msg on socket correctly");
          }
          if(d_socket_type == SOCK_STREAM and
              send(d_socket, &to_send[0], to_send.size(), 0) != to_send.size())
          {
            GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
            throw std::runtime_error("Send failed to send msg on socket correctly");
          }

          std::copy(to_send.begin(), to_send.begin() + difi::DIFI_HEADER_SIZE, d_raw.begin());
          d_full = u_int32_t(pmt::to_long(pmt::dict_ref(tag.value, pmt::mp("full"), pmt::get_PMT_NIL())));
          d_frac = pmt::to_uint64(pmt::dict_ref(tag.value, pmt::mp("frac"), pmt::get_PMT_NIL()));
          d_stream_number = pmt::to_uint64(pmt::dict_ref(tag.value, pmt::mp("stream_num"), pmt::get_PMT_NIL()));
          d_pcks_since_last_reference = 0;
        }
        else if(pmt::eqv(d_pkt_n_key, tag.key))
        {
          d_pkt_n = (d_pkt_n + 1) % difi::VITA_PKT_MOD; // missed packet, so account for this
          d_full = u_int32_t(pmt::to_long(pmt::dict_ref(tag.value, pmt::mp("full"), pmt::get_PMT_NIL())));
          d_frac = pmt::to_uint64(pmt::dict_ref(tag.value, pmt::mp("frac"), pmt::get_PMT_NIL()));
          d_data_len = pmt::to_uint64(pmt::dict_ref(tag.value, pmt::mp("data_len"), pmt::get_PMT_NIL())) - difi::DIFI_HEADER_SIZE;
          if (d_data_len % (2 * d_unpack_idx_size) != 0)
          {
            GR_LOG_WARN(this->d_logger, "data len cannot fit an integer number of samples, something is misconfigured");
          }
          d_samples_per_packet = d_data_len / (2 * d_unpack_idx_size);
          d_out_buf.clear(); // clear the data since we missed samples, start fresh
          d_out_buf.resize(d_data_len);
          d_current_buff_idx = 0;
          d_time_adj = (double)d_samples_per_packet / d_full_samp;
          d_pcks_since_last_reference = 0;
        }
        else if(pmt::eqv(d_static_change_key, tag.key))
        {
          d_static_bits = pmt::to_uint64(tag.value);
        }
      }
    }
    template <class T>
    std::vector<int8_t> difi_sink_cpp_impl<T>::pack_data()
    {
      std::vector<int8_t> to_send(difi::DIFI_HEADER_SIZE + d_out_buf.size());
      u_int32_t full;
      u_int64_t frac;
      std::tie(full, frac) = add_frac_full();
      u_int32_t header = d_static_bits ^ d_pkt_n << 16 ^ (d_data_len + difi::DIFI_HEADER_SIZE) / 4;
      pack_u32(&to_send[0], header);
      std::copy(d_raw.begin() + 8, d_raw.begin() + 16, to_send.begin() + 8);
      pack_u32(&to_send[16], full);
      pack_u64(&to_send[20], frac);
      std::copy(d_out_buf.begin(), d_out_buf.end(), to_send.begin() + difi::DIFI_HEADER_SIZE);
      return to_send;
    }
    template <class T>
    void difi_sink_cpp_impl<T>::send_context()
    {
        if(d_context_packet_size == 108)// this check is a temporary work around for a non-compliant hardware device
        {
            u_int32_t full;
            u_int64_t frac;
            std::tie(full, frac) = add_frac_full();
            pack_u32(&d_context_raw[16], full);
            pack_u64(&d_context_raw[20], frac);
        }
        u_int32_t header = d_context_static_bits ^ d_context_packet_count << 16 ^ (d_context_packet_size / 4);
        pack_u32(&d_context_raw[0], header);
        if(d_socket_type == SOCK_DGRAM and 
            sendto(d_socket, &d_context_raw[0], d_context_raw.size(), 0, (const struct sockaddr *) &d_servaddr, sizeof(d_servaddr)) != d_context_raw.size())
        {
          GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
          throw std::runtime_error("Send failed to send msg on socket correctly");
        }
        if(d_socket_type == SOCK_STREAM and 
            send(d_socket, &d_context_raw[0], d_context_raw.size(), 0) != d_context_raw.size())
        {
          GR_LOG_ERROR(this->d_logger, "Send failed to send msg on socket correctly");
          throw std::runtime_error("Send failed to send msg on socket correctly");
        }
        d_context_packet_count = (d_context_packet_count + 1) % difi::VITA_PKT_MOD;
    }

    template <class T>
    std::tuple<u_int32_t, u_int64_t> difi_sink_cpp_impl<T>::add_frac_full()
    {
      auto frac = d_frac;
      auto full = d_full;
      auto time_adj = d_time_adj * d_pcks_since_last_reference;
      frac += u_int64_t((time_adj - u_int64_t(time_adj)) * difi::PICO_CONVERSION);
      if(frac >= difi::PICO_CONVERSION)
      {
          frac = d_frac % difi::PICO_CONVERSION;
          full += 1;
      }
      full += u_int32_t(time_adj);
      return std::make_tuple(full, frac);
    }
    template <class T>
    void difi_sink_cpp_impl<T>::pack_T(T val)
    {
      auto re = (static_cast<int16_t>(val.real()));
      auto im = (static_cast<int16_t>(val.imag()));
      memcpy(&d_out_buf[d_current_buff_idx], &re, d_unpack_idx_size);
      memcpy(&d_out_buf[d_current_buff_idx + d_unpack_idx_size], &im, d_unpack_idx_size);
    }

    template <class T>
    void difi_sink_cpp_impl<T>::create_udp_socket()
    {
      if ((d_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not make UDP socket, socket may be in use.");
        throw std::runtime_error("Could not make UDP socket");
      }
    }

    template <class T>
    void difi_sink_cpp_impl<T>::create_tcp_socket()
    {
      if ((d_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not make TCP socket, socket may be in use.");
        throw std::runtime_error("Could not make TCP socket");
      }

      fcntl(d_socket, F_SETFL, O_NONBLOCK);
      FD_ZERO(&d_fdset);
      FD_SET(d_socket,&d_fdset);
      connect(d_socket, (struct sockaddr*)&d_servaddr, sizeof(d_servaddr));
    }

    template class difi_sink_cpp<gr_complex>;
    template class difi_sink_cpp<std::complex<char>>;

  } /* namespace azure_software_radio */
} /* namespace gr */

