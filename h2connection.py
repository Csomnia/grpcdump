import logging
import hpack
import struct
from constant import *
import h2frame
import h2stream


class ServerConnection(object):
    """ tcp connection """
    
    def __init__(self, server_end, client_end):
        self.server_end = server_end
        self.client_end = client_end
        self.trans_frame = {
            FRAME_DIR_REQUEST: h2frame.ClientPreface(),
            FRAME_DIR_RESPONSE: h2frame.ServerPreface()
        }
        # self.conn_settings = SettingManager()
        self.all_stream = {}
        self.open_status = True

        # connection's hpack decoder.
        self._req_hpack_decoder = hpack.Decoder()
        self._resp_hpack_decoder = hpack.Decoder()

    def _parse_control_frame(self, frame):
        assert(frame.stream_id == 0)
        assert(frame.frame_type in {
            FRAME_TYPE_SETTINGS,
            FRAME_TYPE_PUSH_PROMISE,
            FRAME_TYPE_PING,
            FRAME_TYPE_GOAWAY,
            FRAME_TYPE_WINDOW_UPDATE,
        })
        logging.info('control frame recv, frame type: %s' % (FRAME_TYPE_STR[frame.frame_type],))

        # navive dump setting frame.
        if FRAME_TYPE_SETTINGS == frame.frame_type:
            logging.info('setting payload: %s' % (frame.frame_payload,))
            assert(len(frame.frame_payload) % 6 == 0)
            pair_num = len(frame.frame_payload) //  6
            st_format = '!' + 'HL' * pair_num
            setting_pair = (struct.unpack(st_format, frame.frame_payload))
            
            for i in range(0, len(setting_pair), 2):
                logging.info(' setting name: %s  value: %s' %
                             (SETTING_TYPE_STR.get(setting_pair[i], 'unknow'),
                              setting_pair[i+1]))
    
    def _dispatch_frame(self, frame, frame_direction):
        if frame.stream_id == 0:
            self._parse_control_frame(frame)
            return
        
        if frame.stream_id not in self.all_stream:
            self.all_stream[frame.stream_id] = h2stream.HTTP2Stream(frame.stream_id)

        logging.info('frame to parse: %s' % (frame, ))
        self.all_stream[frame.stream_id].add_frame(frame, frame_direction)

        logging.info('stream status: %s %s' %
                     (self.all_stream[frame.stream_id]._stream_request_dir_status,
                      self.all_stream[frame.stream_id]._stream_response_dir_status))
        
        if self.all_stream[frame.stream_id].stream_done():
            self.all_stream[frame.stream_id].dump_stream(self._req_hpack_decoder,
                                                         self._resp_hpack_decoder)
            

    def _feed_frame(self, packet_data, frame_direction):
        while packet_data:
            # sanity check: both direction ready to recv.
            assert(not self.trans_frame[frame_direction].frame_done())

            # frame read payload from packet.
            recv_frame = self.trans_frame[frame_direction]
            idx = recv_frame.add_packet(packet_data)
            
            # remove used packet data.
            packet_data = packet_data[idx:]
            
            if recv_frame.frame_done():
                # handle a completed frame.
                if not isinstance(recv_frame, h2frame.ClientPreface):
                    self._dispatch_frame(recv_frame, frame_direction)
                
                # get new frame ready.
                self.trans_frame[frame_direction] = h2frame.HTTP2Frame()
        
    def add_request_packet(self, packet):
        assert(packet.recv_end == self.server_end)
        assert(packet.send_end == self.client_end)
        self._feed_frame(packet.payload, FRAME_DIR_REQUEST)

    def add_response_packet(self, packet):
        assert(packet.recv_end == self.client_end)
        assert(packet.send_end == self.server_end)
        self._feed_frame(packet.payload, FRAME_DIR_RESPONSE)

    def get_key_tuple(self):
        return (self.server_end, self.client_end)

