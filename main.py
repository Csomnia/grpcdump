import sys
import pcapy
import socket
import datetime
import myparser
import mypacket
import myconfig
import logging

from struct import *


logging.basicConfig(level=logging.WARN)
h2parser = myparser.HTTP2Parser()


def main(argv):
    #list all devices
    devices = pcapy.findalldevs()
     
    #ask user to enter device name to sniff
    print("Available devices are :")
    for d in devices :
        print(d)
     
    dev = input("Enter device name to sniff : ")
     
    print("Sniffing device " + dev)
     
    '''
    open device
    # Arguments here are:
    #   device
    #   snaplen (maximum number of bytes to capture _per_packet_)
    #   promiscious mode (1 for true)
    #   timeout (in milliseconds)
    '''
    cap = pcapy.open_live(dev , 65536 , 1 , 0)
 
    #start sniffing packets
    while(1):
        (header, packet) = cap.next()
        #print('%s: captured %d bytes, truncated to %d bytes'
        # %(datetime.datetime.now(), header.getlen(), header.getcaplen()))
        parse_packet(packet)
 

def eth_addr(a):
    """ Convert a string of 6 characters of ethernet address into a dash separated hex string """
    b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (a[0], a[1], a[2], a[3], a[4] , a[5])
    return b


def parse_packet(packet) :
    """ start parse packet."""
     
    #parse ethernet header
    eth_length = 14
     
    eth_header = packet[:eth_length]
    eth = unpack('!6s6sH' , eth_header)
    eth_protocol = socket.ntohs(eth[2])
    logging.info('Destination MAC : ' + eth_addr(packet[0:6]) +
                 ' Source MAC : ' + eth_addr(packet[6:12]) +
                 ' Protocol : ' + str(eth_protocol))

    #Parse IP packets, IP Protocol number = 8
    if eth_protocol == 8 :
        #Parse IP header
        #take first 20 characters for the ip header
        ip_header = packet[eth_length:20+eth_length]
         
        #now unpack them :)
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
 
        version_ihl = iph[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0xF
 
        iph_length = ihl * 4
 
        ttl = iph[5]
        protocol = iph[6]
        s_addr = socket.inet_ntoa(iph[8]);
        d_addr = socket.inet_ntoa(iph[9]);
 
        logging.info('Version : ' + str(version) +
                     ' IP Header Length : ' + str(ihl) +
                     ' TTL : ' + str(ttl) +
                     ' Protocol : ' + str(protocol) +
                     ' Source Address : ' + str(s_addr) +
                     ' Destination Address : ' + str(d_addr))
 
        #TCP protocol
        if protocol == 6:
            t = iph_length + eth_length
            tcp_header = packet[t:t+20]
 
            #now unpack them
            tcph = unpack('!HHLLBBHHH' , tcp_header)
             
            source_port = tcph[0]
            dest_port = tcph[1]
            sequence = tcph[2]
            acknowledgement = tcph[3]
            doff_reserved = tcph[4]
            tcph_length = doff_reserved >> 4
             
            logging.info('Source Port : ' + str(source_port) +
                         ' Dest Port : ' + str(dest_port) +
                         ' Sequence Number : ' + str(sequence) +
                         ' Acknowledgement : ' + str(acknowledgement) +
                         ' TCP header length : ' + str(tcph_length))
             
            h_size = eth_length + iph_length + tcph_length * 4
            data_size = len(packet) - h_size
             
            #get data from the packet
            data = packet[h_size:]

            #simple filter here.
            if myconfig.SERVER_PORT == source_port \
               or myconfig.SERVER_PORT == dest_port:
                logging.info('Data : %s' % data)

                tcp_packet = mypacket.TCPPACKET(src_ip=s_addr,
                                                src_port=source_port,
                                                dest_ip=d_addr,
                                                dest_port=dest_port,
                                                payload=data)
                
                h2parser.recv_tcp_packet(tcp_packet)
              
        print
 
if __name__ == "__main__":
    main(sys.argv)
