import struct
import logging
from constant import *



class HTTP2Frame(object):
    """
    +-----------------------------------------------+
    |                 Length (24)                   |
    +---------------+---------------+---------------+
    |   Type (8)    |   Flags (8)   |
    +-+-------------+---------------+-------------------------------+
    |R|                 Stream Identifier (31)                      |
    +=+=============================================================+
    |                   Frame Payload (0...)                      ...
    +---------------------------------------------------------------+
    sz: 3 + 2 + 4 = 9
    """
    def __init__(self):
        self._frame_complete = False
        self.frame_flags = None
        self.frame_type = None
        self.frame_payload = bytes()
        self.frame_length_remain = 0

    def add_packet(self, packet_data):
        assert(not self.frame_done())
        assert(type(packet_data) == bytes)
        
        offset = 0
        packet_len = len(packet_data)
        if self.frame_length_remain == 0:
            # new frame, then read frame header to member variable.
            frame_length = int.from_bytes(packet_data[:3], byteorder=NETWORK_BYTEORDER, signed=False)
            frame_type, frame_flags, stream_id = struct.unpack('!BBL', packet_data[3:9])
            offset = 9

            self.frame_length_remain = frame_length
            self.frame_type = frame_type
            self.frame_flags = frame_flags
            self.stream_id = stream_id

        
        if packet_len - offset >= self.frame_length_remain:
            # data enough in this tcp packet, close this frame.
            packet_end_idx = offset + self.frame_length_remain
            
            self.frame_payload += packet_data[offset:packet_end_idx]
            self.frame_length_remain -= (packet_end_idx - offset)

            self._frame_complete = True
            return packet_end_idx
        else:
            # not a complete frame.
            packet_end_idx = packet_len
            
            self.frame_payload += packet_data[offset:packet_end_idx]
            self.frame_length_remain -= (packet_end_idx - offset)
            
            return packet_end_idx 

    def frame_done(self):
        """ test if frame recv completed. """
        return self._frame_complete

    def __str__(self):
        """ dumper """
        assert(self.frame_done())
        return "type: {} flags: {:x} stream_id: {} payload: {} "\
            .format(FRAME_TYPE_STR[self.frame_type],
                    self.frame_flags,
                    self.stream_id,
                    self.frame_payload)


class ClientPreface(object):
    """ assure client preface """
    def __init__(self):
        self.client_preface_done = False
    
    def frame_done(self):
        return self.client_preface_done

    def __str__(self):
        return "client preface[{}]".format(HTTP2_CLIENT_PREFACE)

    def add_packet(self, packet_data):
        client_preface_len = len(HTTP2_CLIENT_PREFACE)
        if len(packet_data) < client_preface_len:
            raise Exception('not handle later.')

        if packet_data[:client_preface_len] != HTTP2_CLIENT_PREFACE:
            raise Exception('not illegal client preface. packet: ',
                            packet_data[:client_preface_len])
        
        self.client_preface_done = True
        return client_preface_len

class ServerPreface(HTTP2Frame):
    """ assure first server frame is a setting frame. """
    def add_packet(self, packet_data):
        idx = super().add_packet(packet_data)

        if self.frame_done() and self.frame_type != FRAME_TYPE_SETTINGS:
            raise Exception('not a illega server preface.', self)

        return idx
