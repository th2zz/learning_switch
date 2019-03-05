from switchyard.lib.userlib import *
import time



class LRUCache:
    def _reconnect(self, node):
        node.next.prev=node.prev
        node.prev.nect=node.next

    def _insert(self, node):
        node.next=self.tail
        node.next.prev=node
        node.prev=self.head
        node.prev.next=node

    def __init__(self, size):
        self.size=size
        self.key2node=dict()
        self.head=Node(-1, -1)
        self.tail = Node(-1, -1)
        self.head.next=self.tail
        self.tail.prev=self.head
        self.val2key=dict()
        self.capacity = size

    def getPort(self,key):
        if key not in self.key2node.keys():
            return None #changed
        node=self.key2node[key]
        self._reconnect(node)
        self._insert(node)
        return str(node.val)

    def putItem(self, key, value):
        node=Node
        if value in self.val2key.keys():
            old=self.val2key[value]
            del self.val2key[value]
            node =self.key2node[old_key]
            del self.key2node[old_key]
            self._reconnect(ndoe)
            self.val2key[value]=key

        if key not in self.key2node.keys():
            if len(self.key2node) == self.capacity:
                # be careful about the order of (1) & (2)
                del self.key2node[self.tail.prev.key]  # (1)
                self._reconnect(self.tail.prev)  # (2)
            node = Node(key, value)
            self.key2node[key] = node


        else:
              node = self.key2node[key]
              node.val = value
              self._reconnect(node)
        self._insert(node)

class Node:
        def __init__(self,key,val):
            self.prev = None
            self.next = None
            self.key=key
            self.val=val


def main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    #table is splited as 2 parts for simplcity
    forwarding_table = {}#table that contains info about addr and port
    time_table = {}#table that associate each addr with its time 

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
            time_table.update({header.src: time.time()})#add mru entry simultanously in 2 tables
            forwarding_table.update({header.src: input_port})#add mru entry simultanously in 2 tables
        else:
            if(input_port != forwarding_table.get(header.src)):#incoming port info becomes different, update
                forwarding_table[header.src] = input_port
        dest_port = forwarding_table.get(header.dst)
        if header.dst in mymacs:#dest is my switch
            log_debug("Packet intended for me")
        elif dest_port is not None:#entry exists
            time_table.update({header.dst: time.time()})#update it to be the mru entry
            net.send_packet(dest_port, packet)
        else:#no entry for dest, flood packet to all ports except incoming
            for intf in my_interfaces:
                if input_port != intf.name:
                    log_debug("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
