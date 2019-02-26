testfiles:
hubtests.py     should failed    
lru_test.srpy    passed
myswitchstp_test_release.py

swyard -t test.py/test.srpy myfile/myfile.py     
-v for verbose option

To run your switch in Mininet, run the switchtopo.py custom topology script. It will create a small network consisting of a single switch with three hosts (client, server1, and server2) in the following configuration (note that only IP addresses of the 3 hosts are shown in the picture; Ethernet MAC addresses for each interface (6 interfaces total) are not shown).

To start up Mininet using this script, just type:

$ sudo python switchtopo.py

Once Mininet starts up, you should open a terminal window on the Mininet node named "switch":

mininet> xterm switch

In the window that opens, run your switch in "real" (non-test) mode:

# swyard myswitch.py

Note that to run swyard in Mininet in a root shell (such as the shell that is open in response to the xterm command), you will need to activate the Python virtual environment which has Switchyard installed in it. Refer to the Switchyard documentation for more information.

To examine whether your switch is behaving correctly, you can do the following:

    Open terminals on client and server1 (xterm client and xterm server1 from the Mininet prompt)
    In the server1 terminal, run wireshark -k. Wireshark is a program that allows you to "snoop" on network traffic arriving on a network interface. We'll use this to verify that we see packets arriving at server1 from client.
    In the terminal on the client node, type ping -c 2 192.168.100.1. This command will send two "echo" requests to the server1 node. The server1 node should respond to each of them if your switch is working correctly. You should see at the two echo request and echo replies in wireshark running on server1, and you will probably see a couple other packets (e.g., ARP, or Address Resolution Protocol, packets).
    If you run wireshark on server2, you should not see the echo request and reply packets (but you will see the ARP packets, since they are sent with broadcast destination addresses).

