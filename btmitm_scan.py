import bluetooth, time
from btmitm_utils import *


def scan(detailed=False):
    nearby_devices = bluetooth.discover_devices(lookup_names=True, lookup_class=True)
    print("found %d devices" % len(nearby_devices))
    for addr, name,clas in nearby_devices:
        print("%s - %s (0x%x)" % (addr, name, clas))

        if detailed:
            services = bluetooth.find_service(address=addr)
            for svc in services:
                print_service(svc)
        print('')

def l2cap_channel_scan(addr):
    """
        l2cap channels are odd numbers between
            1-4095 for reserved ports
            4097-32765 for dynamic ports
    """
    open_ports = []
    for i in range(1,4095+1,2):
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            #print('connecting on '+hex(i))
            sock.connect((addr,i))
            open_ports.append(i)
            print(open_ports)
            #raw_input()
            sock.close()
        except Exception as e: 
            #print(e)
            pass
        #time.sleep(1)
    print('Open ports on '+ addr + '', open_ports)


