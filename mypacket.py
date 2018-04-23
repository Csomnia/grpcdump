class TCPPACKET(object):
    def __init__(self,
                 src_ip=None,
                 src_port=None,
                 dest_ip=None,
                 dest_port=None,
                 payload=None):
        self.src_ip = src_ip
        self.dest_ip = dest_ip
        self.src_port = src_port
        self.dest_port = dest_port

        self.send_end = (self.src_ip, self.src_port)
        self.recv_end = (self.dest_ip, self.dest_port)

        self.payload = payload


