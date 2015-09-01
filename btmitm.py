#!/usr/bin/env python

import sys
from argparser import args,parser
from btmitm_mitm import Btmitm
from btmitm_scan import *
from btmitm_adapter import *


if args.addr_master and args.addr_slave:
    print 'Running MiTM on master ', args.addr_master, ' and slave ', args.addr_slave
    btmitm = Btmitm(target_master = args.addr_master,
                    target_slave = args.addr_slave,
                    already_paired = args.skip
                    )
    btmitm.mitm()

elif args.set_address or args.set_class or args.set_name: 
    if not args.bluetooth:
        print('Specify which interface to use (-b)')
        sys.exit()
    if args.set_address:
        adaptor_address(args.bluetooth,args.set_address)
    if args.set_class:
        adaptor_class(args.bluetooth,args.set_class)
    if args.set_name:
        adaptor_name(args.bluetooth,args.set_name)


elif args.list:
    print('Run "hcitool dev" to see adaptors')
    print('Run "hciconfig -a" to see more adaptor information')
else:
    parser.print_help()


