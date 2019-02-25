from switchyard.lib.userlib import *
import time


def main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    forwarding_table = {}
    time_table = {}

    while True:
        try:
            timestamp, input_port, packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return
        header = packet[0];#Ethernet header Packet[Ethernet]

        if (header.src not in forwarding_table):#src addr not in table
            if (len(time_table) >= 5):#full, remove lru entry
                sorted_keys = sorted(time_table, key=time_table.get)#sort dict based on value and put keys in order in this list
                lru_key = sorted_keys[0]
                del time_table[lru_key]
                del forwarding_table[lru_key]
            time_table.update({header.src: time.time()})#keep a record of current header src addr & time
        forwarding_table.update({header.src: input_port})#add mru entry
        
        dest_port = forwarding_table.get(header.dst)
        if header.dst in mymacs:#dest is my switch
            log_debug("Packet intended for me")
        elif dest_port is not None:
            net.send_packet(dest_port, packet)
            time_table.update({header.dst: time.time()})
        else:#dest port not present in table, flood packet to all ports except incoming
            for intf in my_interfaces:
                if input_port != intf.name:
                    log_debug("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
