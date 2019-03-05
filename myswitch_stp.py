from time import sleep
from spanningtreemessage import SpanningTreeMessage
from switchyard.lib.userlib import *
import sys
import struct
import myswitch_lru

flood_address='FF:FF:FF:FF:FF:FF'
FORWARD = True
BLOCK = False

#Fuction: generate normal packets

def normal_packet(hwsrc,hwdst, ipsrc, ipdst, r_flag=False):
    ip_packet=IPv4(src=ipsrc, dst=ipdst, protocol=IPProtocol.ICMP, ttl=32)
    ether=Ethernet(src=hwsrc, dst=hwdst, ethertype=EtherType.IP)
    icmp_packet=ICMP()
    if r_flag:
        icmp_packet.icmptype=ICMPType.EchoReply
    else:
        icmp_packet.icmptype=ICMPType.EchoRequest
    return ether+ip_packet+icmp_packet

#Fuction: generate STP packets
def stp_packet (root_id, hops, src, dst):
    SPM=SpanningTreeMessage(root=root_id,hops_to_root=hops)
    Ethernet.add_next_header_class(EtherType.SLOW,SpanningTreeMessage)
    packet= Ethernet(src=src, dst=dst, ethertype=EtherType.SLOW) +SPM
    xbytes=packet.to_bytes()
    p=Packet(raw=xbytes)
    return p

def check_packet(packet_str):
    s=set(packet_str.split(' '))
    if "SpanningTreeMessage" in s:
        return True
    else:
        return False


def parse(packet_str):
    arr=packet_str.split(' ')
    root=None
    hops=None
    i=0
    while i<len(arr):
        if arr[i]=="(root:":
            root=arr[i+1]
            root="".join(root[k] for k in range(len(root)-1))
            i+=2
        elif arr[i]=="hops-to-root:":
            hops=arr[i+1]
            hops="".join(hops[k] for k in range(len(hops)-1))
            hops=int(hops)
            i+=2
        else:
            i+=1

    if root==None or hops ==None:
        print("Error: did not get root or hops or both")

    return root, hops

class SwitchData:
    def __init__(self, id, hops_to_root, ports):
        self.id=EthAddr(id)
        self.hops=hops_to_root
        self.root=EthAddr(id)
        self.blocked_port_set=set()
    def update(self, new_root, new_hops, input_port):
        new_root = EthAddr(new_root)#add
        if new_root > self.root:
            return False
        elif new_root<self.root:
            self.root = new_root
            self.hops= new_hops+1
            return True
        else:
            if new_hops + 1 < self.hops:
                self.hops = new_hops + 1
                return True
            elif new_hops + 1 > self.hops:
                return False
            else:
                self.blocked_port_set.add(input_port)
                return False


def main(net):
    interface=net.interfaces()
    ports=set([intf.name for intf in interface])
    address=set([intf.ethaddr for intf in interface])

    lru = myswitch_lru.LRUCache (5)

    sw_data=SwitchData(min(address),0,ports)

    for intf in interface:
        net.send_packet(intf.name, stp_packet(sw_data.root, sw_data.hops, sw_data.id, flood_address))

    while True:
        try:
            timestamp, input_port, packet = net.recv_packet()
        except NoPackets:
            log_debug("Did not receive packets.")

            sleep(2)
            for intf in interface:
                net.send_packet(intf.name, stp_packet(sw_data.root, sw_data.hops, sw_data.id, flood_address))
            continue
        except Shutdown:
            log_debug("Received the shut down signal")
            return

        pkt_str = str(packet)
        is_stp_pkt = check_packet(pkt_str)
        if is_stp_pkt:
            new_root, new_hops = parse(pkt_str)
            to_flood = sw_data.update(new_root, new_hops, input_port)
            if to_flood:
                for intf in interface:
                    if intf.name != input_port:
                        net.send_packet(intf.name, stp_packet(sw_data.root, sw_data.hops, sw_data.id, flood_address))
        else:

            lru.putItem(packet[0].src, input_port)

            if packet[0].dst in address:
                log_debug("Packet intended for me")
            else:
                output_port = lru.getPort(packet[0].dst)
                if output_port is not None:
                    net.send_packet(output_port, packet)
                else:
                    for intf in interface:
                        if intf.name != input_port and intf.name not in sw_data.blocked_port_set:
                            net.send_packet(intf.name, packet)
    net.shutdown()


