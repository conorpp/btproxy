from __future__ import print_function
import re, struct, binascii

def master_cb(req):
    """
        Received something from master, 
        about to be sent to slave.

        Put all manipulations for packet here.

        req is the incoming packet as a byte array
        starting with the length of packet at offset 0x0
    """
    print( '<< ', repr(req))
    open('mastermessages.log', 'a+b').write(req)
    return req

def slave_cb(res):
    """
        Same as above but it's from slave
        about to be sent to master
    """
    print('>> ', repr(res))
    open('slavemessages.log', 'a+b').write(res)
    return res

# get a formated hex representation of byte array
def tohex(s):
    s= ' '.join([format(ord(x),'x') for x in s])
    return re.sub("(.{64})", "\\1\n", s, 0, re.DOTALL)


def example_master_to_slave_pebble_watch_cb(s):
    """
        Replace text in pebble messages with
        troll messages
    """
    for i in [
              ('open on phone','YOU HAVE BEEN'),
              ('dismiss', 'HACKED '),
              ('reply', '!@#$%'),
              ]:
        replacee= i[0]
        replacew = i[1]
        if replacee in s.lower(): 
            s = s.lower().replace(replacee,replacew)
            s = update_spp_packet_length(s)
    return s

def update_spp_packet_length(s):
    """
        Updates the length part of header in
        spp packet.  This should be used if
        the length changes after manipulation
    """
    l = len(s) - 4
    s = list(s)
    return ''.join([struct.pack('!H', l)] + s[2:])


# Wrapper functions for catching errors
def btproxy_master_cb(req):
    try: 
        req = master_cb(req)
        assert req is not None
    except Exception as e: print(e)
    return req

def btproxy_slave_cb(res):
    try: 
        res = slave_cb(res)
        assert res is not None
    except Exception as e: print(e)
    return res
