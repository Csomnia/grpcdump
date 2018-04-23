import myconfig
import logging
import h2connection
from constant import *


def get_packet_type(tcp_packet):
    """ get packet type -> request packet or response packet. 

        navive implementation, only use port for consideration.
    """
    if tcp_packet.src_port == myconfig.SERVER_PORT:
        return FRAME_DIR_RESPONSE
    elif tcp_packet.dest_port == myconfig.SERVER_PORT:
        return FRAME_DIR_REQUEST
    else:
        raise Exception('both src port({}) and dest port({}) are not equal to server port({}).'
                        .format(tcp_packet.src_port, tcp_packet.dest_port, myconfig.server_port))


class HTTP2Parser(object):
    def __init__(self):
        self.all_connection = {}

    def recv_tcp_packet(self, tcp_packet):
        """ recv tcp packet.
            rule. packet with http2 preface or already in
            a active connection.
        """
        # get packet direction.
        tcp_packet_dir_type = get_packet_type(tcp_packet)
        
        if tcp_packet_dir_type == FRAME_DIR_REQUEST:
            conn_key = (tcp_packet.recv_end, tcp_packet.send_end)
        elif tcp_packet_dir_type == FRAME_DIR_RESPONSE:
            conn_key = (tcp_packet.send_end, tcp_packet.recv_end)

        # if this connection not establish.
        if conn_key not in self.all_connection:
            new_connection = h2connection.ServerConnection(server_end=conn_key[0],
                                                           client_end=conn_key[1])
            self.all_connection[conn_key] = new_connection

        conn = self.all_connection[conn_key]

        # handle packet.
        if tcp_packet_dir_type == FRAME_DIR_REQUEST:
            conn.add_request_packet(tcp_packet)
        elif tcp_packet_dir_type == FRAME_DIR_RESPONSE:
            conn.add_response_packet(tcp_packet)
