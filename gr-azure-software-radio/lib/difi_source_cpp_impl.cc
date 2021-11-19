// -*- c++ -*-
// Copyright (c) Microsoft Corporation.
// Licensed under the GNU General Public License v3.0 or later.
// See License.txt in the project root for license information.

#include <gnuradio/io_signature.h>
#include "difi_source_cpp_impl.h"
#include <functional>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <sys/poll.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <errno.h>

#define NUM_BYTES_PER_WORD (4)

namespace gr {
  namespace azure_software_radio {

    u_int32_t unpack_u32(u_int8_t *start)
    {
      u_int32_t val;
      memcpy(&val, start, sizeof(val));
      return ntohl(val);
    }
    u_int64_t unpack_u64(u_int8_t *start)
    {
      u_int64_t val;
      memcpy(&val, start, sizeof(val));
      return be64toh(val);
    }

      u_int32_t unpack_u32(int8_t *start)
    {
      u_int32_t val;
      memcpy(&val, start, sizeof(val));
      return ntohl(val);
    }
    u_int64_t unpack_u64(int8_t *start)
    {
      u_int64_t val;
      memcpy(&val, start, sizeof(val));
      return be64toh(val);
    }

    template <class T>
    typename difi_source_cpp<T>::sptr difi_source_cpp<T>::make(std::string ip_addr, uint32_t port, uint8_t socket_type, uint32_t stream_number, int bit_depth)
    {
      return gnuradio::make_block_sptr<difi_source_cpp_impl<T>>(ip_addr, port, socket_type, stream_number, bit_depth);
    }

    template <class T>
    difi_source_cpp_impl<T>::difi_source_cpp_impl(std::string ip_addr, uint32_t port, uint8_t socket_type, uint32_t stream_number, int bit_depth)
        : gr::sync_block("source_cpp", gr::io_signature::make(0, 0, 0),
                         gr::io_signature::make(1 /* min outputs */,
                                                1 /*max outputs */,
                                                sizeof(T))),
          d_ip_addr(ip_addr),
          d_port(port),
          d_stream_number(stream_number)

    {
      d_tv.tv_sec = 0;
      d_tv.tv_usec = 100000;
      d_packet_buffer.resize(9000);
      memset(&d_servaddr, 0, sizeof(d_servaddr));
      d_servaddr.sin_family = AF_INET;
      d_servaddr.sin_port = htons(port);
      d_servaddr.sin_addr.s_addr = INADDR_ANY;
      d_socket_type = (socket_type == 1) ?  SOCK_STREAM : SOCK_DGRAM;
      d_client_socket = -1;

      if(d_socket_type == SOCK_DGRAM)
      {
        create_udp_socket();
      }
      else
      {
        create_tcp_socket();
      }

      d_context = NULL;
      d_last_pkt_n = -1;
      d_static_bits = -1;
      this->set_output_multiple(9000);
      d_unpack_idx_size = bit_depth == 8 ? 1 : 2;

      d_unpacker = unpack_16<T>;
      if(d_unpack_idx_size == 1)
          d_unpacker = &unpack_8<T>;
    }

    template <class T>
    difi_source_cpp_impl<T>::~difi_source_cpp_impl()
    {
      if(d_socket_type == SOCK_STREAM)
      {
        close(d_client_socket);
        FD_CLR(d_socket,&d_rset);
      }

      close(d_socket);
    }

    template <class T>
    int difi_source_cpp_impl<T>::work(int noutput_items,
                              gr_vector_const_void_star &input_items,
                              gr_vector_void_star &output_items)
    {
      T *out = reinterpret_cast<T *>(output_items[0]);
      return buffer_and_send(out, noutput_items);
    }

    template <class T>
    int difi_source_cpp_impl<T>::buffer_and_send(T *out, int noutput_items)
    {
      boost::this_thread::disable_interruption disable_interrupt;
      socklen_t len = sizeof(d_servaddr);
      int size_gotten = -1;
      if(d_socket_type == SOCK_DGRAM)
      {
        size_gotten = recvfrom(d_socket, &d_packet_buffer[0], d_packet_buffer.size(),
                                  MSG_WAITALL, (struct sockaddr *)&d_servaddr, &len);
      }
      else
      {
        size_gotten = recv_tcp_packet();
      }

      if(size_gotten <= 0)
      {
        return 0;
      }

      if (size_gotten % (d_unpack_idx_size * 2) != 0)
      {
        GR_LOG_WARN(this->d_logger, "got a packet which is not divisible by the number bytes per sample, samples will be lost. Check your bit depth configuration.");
      }
      header_data header;
      parse_header(header);
      if (d_stream_number != -1 and header.stream_num != d_stream_number)
      {
        GR_LOG_WARN(this->d_logger, "got wrong stream number, " + std::to_string(header.stream_num) + " expected " + std::to_string(d_stream_number));
        return 0;
      }
      if (header.type == 1 and d_last_pkt_n != -1 and (d_last_pkt_n + 1) % VITA_PKT_MOD != header.pkt_n)
      {
        GR_LOG_WARN(this->d_logger, "got an out of order packet, " + std::to_string(header.pkt_n) +  " expected " + std::to_string((d_last_pkt_n + 1) % VITA_PKT_MOD));
        this->add_item_tag(0, this->nitems_written(0), pmt::intern("pck_n"), make_pkt_n_dict(header.pkt_n, size_gotten));
      }
      if (d_last_pkt_n == -1 and header.type == 1)
      {
        this->add_item_tag(0, this->nitems_written(0), pmt::intern("pck_n"), make_pkt_n_dict(header.pkt_n, size_gotten));
      }
      if (header.type == 1) // one is a data packet (see DIFI spec)
      {
        uint32_t items_written = 0;
        int out_items = std::min((size_gotten - static_cast<int>(difi::DATA_START_IDX)) / 2, noutput_items);
        d_last_pkt_n = header.pkt_n;
        if (d_context != NULL)
        {
          this->add_item_tag(0, this->nitems_written(0) + d_deque.size(), pmt::intern("context"), d_context);
          d_context = NULL;
        }

        uint32_t idx = difi::DATA_START_IDX; //start after the data header
        while (items_written < out_items and idx < size_gotten)
        {
          T sample = d_unpacker(&d_packet_buffer[idx]);
          out[items_written] = sample;
          idx += 2 * d_unpack_idx_size;
          items_written++;
        }
        return items_written;
      }
      else
      {
        d_context = make_context_dict(header, size_gotten);
        return buffer_and_send(out, noutput_items);
      }
    }

    template <class T>
    void difi_source_cpp_impl<T>::parse_header(header_data &data)
    {
      auto header = unpack_u32(&d_packet_buffer[0]);
      auto stream_number = unpack_u32(&d_packet_buffer[4]);
      auto full = unpack_u32(&d_packet_buffer[16]);
      auto frac = unpack_u64(&d_packet_buffer[20]);
      data.type = header >> 28;
      data.pkt_n = (header >> 16) & 0xf;
      data.header = header;
      data.stream_num = stream_number;
      int32_t static_part = header & 0xfff00000;
      if(data.type == 1)
      {
        d_last_frac = frac;
        d_last_full = full;
        if(d_static_bits != static_part)
        {
          d_static_bits = static_part;
          this->add_item_tag(0, this->nitems_written(0), pmt::intern("static_change"), pmt::from_uint64(static_part));
        }
      }
    }

    template <class T>
    pmt::pmt_t difi_source_cpp_impl<T>::make_pkt_n_dict(int pkt_n, int size_gotten)
    {
      pmt::pmt_t dict = pmt::make_dict();
      auto full = unpack_u32(&d_packet_buffer[16]);
      auto frac = unpack_u64(&d_packet_buffer[20]);
      dict = pmt::dict_add(dict, pmt::intern("pck_n"), pmt::from_uint64((u_int64_t)pkt_n));
      dict = pmt::dict_add(dict, pmt::intern("data_len"), pmt::from_uint64(size_gotten));
      dict = pmt::dict_add(dict, pmt::intern("full"), pmt::from_long(full));
      dict = pmt::dict_add(dict, pmt::intern("frac"), pmt::from_uint64(frac));
      return dict;
    }

    template <class T>
    pmt::pmt_t difi_source_cpp_impl<T>::make_context_dict(header_data &header, int size_gotten)
    {
      pmt::pmt_t pmt_dict = pmt::make_dict();
      context_packet context;
      if(size_gotten == 72)
      {
        unpack_context_alt(context);
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("header"), pmt::from_long(header.header));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("stream_num"), pmt::from_uint64(header.stream_num));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("class_id"), pmt::from_long(context.class_id));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("full"), pmt::from_long(d_last_full));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("frac"), pmt::from_uint64(d_last_frac));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("CIF"), pmt::from_long(context.cif));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("bandwidth"), pmt::from_double(context.bw));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("if_reference_frequency"), pmt::from_uint64(context.if_ref_freq));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("rf_reference_frequency"), pmt::from_uint64(context.rf_ref_freq));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("if_band_offset"), pmt::from_uint64(context.if_band_offset));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("samp_rate"), pmt::from_double(context.samp_rate));;
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("state_and_event_indicator"), pmt::from_long(context.state_indicators));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("data_packet_payload_format"), pmt::from_uint64(context.payload_format));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("raw"), pmt::init_s8vector(size_gotten, &d_packet_buffer[0]));
      }
      else
      {
        unpack_context(context);
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("header"), pmt::from_long(header.header));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("stream_num"), pmt::from_uint64(header.stream_num));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("class_id"), pmt::from_long(context.class_id));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("full"), pmt::from_long(context.full));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("frac"), pmt::from_uint64(context.frac));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("CIF"), pmt::from_long(context.cif));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("reference_point"), pmt::from_long(context.ref_point));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("bandwidth"), pmt::from_double(context.bw));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("if_reference_frequency"), pmt::from_uint64(context.if_ref_freq));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("rf_reference_frequency"), pmt::from_uint64(context.rf_ref_freq));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("if_band_offset"), pmt::from_uint64(context.if_band_offset));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("reference_level"), pmt::from_long(context.ref_lvl));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("gain"), pmt::from_long(context.gain));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("samp_rate"), pmt::from_double(context.samp_rate));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("timestamp_adjustment"), pmt::from_uint64(context.t_adj));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("timestamp_calibration_time"), pmt::from_uint64(context.t_cal));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("state_and_event_indicator"), pmt::from_long(context.state_indicators));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("data_packet_payload_format"), pmt::from_uint64(context.payload_format));
        pmt_dict = pmt::dict_add(pmt_dict, pmt::intern("raw"), pmt::init_s8vector(size_gotten, &d_packet_buffer[0]));
      }
      if ((context.payload_format >> 32 & 0x0000001f) + 1 != d_unpack_idx_size * 8)
      {
        GR_LOG_ERROR(this->d_logger, "The context packet bit depth does not match the input bit depth, check your configuration.\nContext packet bit depth is: " + std::to_string((context.payload_format >> 32 & 0x0000001f) + 1));
        throw std::runtime_error("The context packet bit depth does not match the input bit depth, check your configuration.\nContext packet bit depth is: " + std::to_string((context.payload_format >> 32 & 0x0000001f) + 1));
      }
      return pmt_dict;
    }

    template <class T>
    void difi_source_cpp_impl<T>::unpack_context_alt(context_packet &context)
    {
      int idx = 0;
      context.class_id = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.cif = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.bw = parse_vita_fixed_double(unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]));
      context.if_ref_freq = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.rf_ref_freq = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.if_band_offset = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.samp_rate = parse_vita_fixed_double(unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]));
      context.state_indicators = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
      context.payload_format = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_ALT_OFFSETS[idx++]]);
    }
    template <class T>
    void difi_source_cpp_impl<T>::unpack_context(context_packet &context)
    {
      int idx = 0;
      context.class_id = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.full = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.frac = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.cif = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.ref_point = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.bw = parse_vita_fixed_double(unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]));
      context.if_ref_freq = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.rf_ref_freq = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.if_band_offset = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.ref_lvl = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.gain = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.samp_rate = parse_vita_fixed_double(unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]));
      context.t_adj = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.t_cal = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.state_indicators = unpack_u32(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
      context.payload_format = unpack_u64(&d_packet_buffer[difi::CONTEXT_PACKET_OFFSETS[idx++]]);
    }

    template <class T>
    void difi_source_cpp_impl<T>::create_udp_socket()
    {

      if ((d_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not make UDP socket, socket may be in use.");
        throw std::runtime_error("Could not make UDP socket");
      }

      int sock_b_size = 2000000;
      if(setsockopt(d_socket, SOL_SOCKET, SO_RCVBUF, &sock_b_size, sizeof(sock_b_size)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not set socket size");
        throw std::runtime_error("Could not set socket size");
      }

      if (setsockopt(d_socket, SOL_SOCKET, SO_RCVTIMEO, &d_tv, sizeof(d_tv)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not set timeout on socket");
        throw std::runtime_error("Could not set timeout on socket");
      }

      if (bind(d_socket, (const struct sockaddr *)&d_servaddr,
               sizeof(d_servaddr)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not connect to port, port may be in use");
        throw std::runtime_error("Could not connect to port");
      }
    }

    template <class T>
    void difi_source_cpp_impl<T>::create_tcp_socket()
    {

      if ((d_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not make TCP socket, socket may be in use.");
        throw std::runtime_error("Could not make TCP socket");
      }

      int sock_b_size = 2000000;
      if(setsockopt(d_socket, SOL_SOCKET, SO_RCVBUF, &sock_b_size, sizeof(sock_b_size)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not set socket size");
        throw std::runtime_error("Could not set socket size");
      }

      if (setsockopt(d_socket, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &d_tv, sizeof(d_tv)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not set timeout on socket");
        throw std::runtime_error("Could not set timeout on socket");
      }

      if (setsockopt(d_socket, SOL_SOCKET, SO_RCVTIMEO, &d_tv, sizeof(d_tv)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not set timeout on socket");
        throw std::runtime_error("Could not set timeout on socket");
      }

      if (bind(d_socket, (const struct sockaddr *)&d_servaddr,
               sizeof(d_servaddr)) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Could not connect to port, port may be in use");
        throw std::runtime_error("Could not connect to port");
      }

      if(listen(d_socket, 1) < 0)
      {
        GR_LOG_ERROR(this->d_logger, "Error while listening to incoming connections");
        throw std::runtime_error("Error while listening to incoming connections");
      }

      FD_ZERO(&d_rset);
      FD_SET(d_socket, &d_rset);
      d_client_socket = -1;
    }

    template <class T>
    void difi_source_cpp_impl<T>::reset_tcp_connection()
    {
      close(d_client_socket);
      FD_CLR(d_client_socket, &d_rset);
      d_client_socket = -1;
      GR_LOG_DEBUG(this->d_logger, "Connection lost");
    }

    template <class T>
    int difi_source_cpp_impl<T>::recv_tcp_packet()
    {
      if(is_tcp_socket_ready())
      {
        // read the first word to determine the size of the packet
        int size_gotten = tcp_readall(&d_packet_buffer[0],NUM_BYTES_PER_WORD);

        if(size_gotten == NUM_BYTES_PER_WORD)
        {
          // compute the number of bytes per packet
          // per DIFI version 1.0.0 spec each packet contains the packet size (number of 32-bit words) in the header
          // Packet Size: Bits 0-15
          // check packet size
          auto header = unpack_u32(&d_packet_buffer[0]);
          int pkt_size = NUM_BYTES_PER_WORD * (header&0xffff);
          int32_t num_bytes_to_read = pkt_size - NUM_BYTES_PER_WORD;

          return size_gotten + tcp_readall(&d_packet_buffer[NUM_BYTES_PER_WORD],num_bytes_to_read);
        }
      }
      return 0;
    }

    template <class T>
    bool difi_source_cpp_impl<T>::is_tcp_socket_ready()
    {
      if(d_client_socket >= 0)
        return true;
      else
      {
        // select file descriptors that we want to monitor (server socket)
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(d_socket,&read_fds);

        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 100000;

        int status = select(d_socket+1, &read_fds, NULL, NULL, &tv);
        if (status < 0)
        {
          // get the error code from the file descriptor
          int error_code;
          socklen_t len = sizeof(error_code);
          getsockopt(d_socket, SOL_SOCKET, SO_ERROR, &error_code, &len);

          GR_LOG_ERROR(this->d_logger, "Could not select file descriptor - (server file descriptor error code: " + std::to_string(error_code) + ")");
          throw std::runtime_error("Could not select file descriptor - (server file descriptor error code: " + std::to_string(error_code) + ")");
        }
        // accept incoming connection if client has not connected yet
        if(FD_ISSET(d_socket, &read_fds))
        {
          socklen_t addrlen = sizeof(d_servaddr);
          d_client_socket = accept(d_socket, (struct sockaddr*)&d_servaddr, &addrlen);

          if (d_client_socket < 0)
          {
            GR_LOG_ERROR(this->d_logger, "Could not accept incoming connection");
            throw std::runtime_error("Could not accept incoming connection");
          }

          FD_SET(d_client_socket, &d_rset);
          return true;
        }
        return false;
      }
    }

    template <class T>
    int difi_source_cpp_impl<T>::tcp_readall(int8_t* buf, int len)
    {
      int num_received = 0;
      int num_to_read = len;

      struct timeval begin, end;
      gettimeofday(&begin,0);

      while(num_received < len)
      {
        // select file descriptors that we want to monitor (socket client)
        fd_set read_fds;
        FD_ZERO(&read_fds);
        FD_SET(d_client_socket,&read_fds);

        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 100000;
        int status = select(d_client_socket+1, &read_fds, NULL, NULL, &tv);
        if (status < 0)
        {
          // get the error code from the file descriptor
          int error_code;
          socklen_t len = sizeof(error_code);

          getsockopt(d_client_socket, SOL_SOCKET, SO_ERROR, &error_code, &len);
          GR_LOG_ERROR(this->d_logger, "Could not select client file descriptor -  (error code: " + std::to_string(error_code) + ")");
          throw std::runtime_error("Could not select client file descriptor -  (error code: " + std::to_string(error_code) + ")");
        }

        // check if there is data in the socket buffer
        if(FD_ISSET(d_client_socket, &read_fds))
        {
          int size_gotten = recv(d_client_socket,buf+num_received,num_to_read,MSG_WAITALL);

          // when monitoring the file descriptor using 'select' and the fd is set, there should be
          // bytes in the socket buffer. If the receive call returns 0 bytes then the connection has
          // been lost and the client needs to re-connect
          if(size_gotten <= 0)
          {
            reset_tcp_connection();
            return 0;
          }

          num_to_read = len-num_received;
          num_received += size_gotten;
        }

        gettimeofday(&end,0);
        long seconds = end.tv_sec - begin.tv_sec;
        long microseconds = end.tv_usec - begin.tv_usec;
        long time_elapsed = seconds * 1e6 + microseconds;
        if(time_elapsed > d_tv.tv_usec)
        {
          if(num_received > 0 and num_received != len)
          {
            GR_LOG_WARN(this->d_logger, "Read timeout error - could not receive the expected number of bytes for a packet. Expected: "
            + std::to_string(len) + " Received: " + std::to_string(num_received));
          }
          break;
        }
      }

      return num_received;
    }

    template class difi_source_cpp<gr_complex>;
    template class difi_source_cpp<std::complex<char>>;

  } /* namespace azure_software_radio */
} /* namespace gr */
