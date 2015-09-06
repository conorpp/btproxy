# Command line interface
from __future__ import print_function

from . import argparser
args = argparser.args
import subprocess,sys,re,imp,os
import bluetooth, clone

def _run(cmd):
    try:
        if args.verbose:
            print('running ', cmd)
        return subprocess.check_output(cmd)
    except Exception as e:
        print(e, cmd)
        raise RuntimeError( ' '.join(cmd)+' failed')

def restart_bluetoothd():
    _run(['replace_bluetoothd'])

def instrument_bluetoothd():
    _run(['replace_bluetoothd',imp.find_module('blocksdp')[1]])

def inquire(addr):
    return parse_inq(_run(['sdptool','records', addr]), addr)

def enable_adapter(adapt, cond=True):
    _run(['hciconfig',adapt, 'up' if cond else 'down'])

def reset_adapter(adapt):
    _run(['hciconfig',adapt, 'reset'])

def advertise_adapter(adapt, cond=True):
    _run(['hciconfig',adapt, 'piscan' if cond else 'pscan'])

def pair_adapter(adapt, addr):
    path = _run(['which','bluez_simple_agent_nouser']).strip()
    _run(['python', path, adapt, addr])

def enable_adapter_ssp(adapt, cond):
    _run(['hciconfig',adapt,'sspmode','1' if cond else '0'])


def list_adapters():
    s = _run(['hciconfig','-a'])
    return re.compile(r'(hci[0-9]+):').findall(str(s))

def lookup_info(addr, **kwargs):
    Class = kwargs.get('Class',True)
    Name = kwargs.get('Name',True)
    Address = kwargs.get('Address',True)
    info = {}
    while True:
        s = _run(['hcitool','inq'])
        for i in s.splitlines():
            i = str(i)
            if addr in i:
                info['class'] = re.compile(r'class: ([A-Fa-fx0-9]*)').findall(i)[0]
                info['addr'] = addr
                info['name'] = bluetooth.lookup_name(addr)
                return info

        print( 'Still looking for ', addr,'...', ' Is it discoverable? ')


def adapter_address(inter, addr=None):
    if addr is not None:
        inter = int(str(inter).replace('hci',''))
        if (bluetooth.is_valid_address(addr)):
            print('device set to ' + clone.set_adapter_address(inter,addr))
        else:
            raise ValueError('Invalid Address: '+addr);
    else:
        s = _run(['hciconfig',inter])
        return re.compile(r'Address: ([A-Fa-f0-9:]*)').findall(str(s))[0]

def adapter_class(inter, clas=None):
    if clas is not None:
        s = _run(['hciconfig',inter, 'class', clas])
        return s
        #clone.set_adapter_class(inter,clas);
    else:
        s = _run(['hciconfig',inter, 'class'])
        return re.compile(r'Class: ([A-Fa-fx0-9]*)').findall(str(s))[0]

def adapter_name(inter, name=None):
    if name is not None:
        #inter = int(str(inter).replace('hci',''))
        #clone.set_adapter_name(inter,name);
        s = _run(['hciconfig',inter, 'name', name])
    else:
        s = _run(['hciconfig',inter, 'name'])
        return re.compile(r'Name: \'(.*)\'').findall(str(s))[0]


def parse_inq(inq,target):
    inq = inq.decode('utf-8')
    lines = inq.split('\n')
    services = []
    device = {'host': target, 'description': 'btproxy',
                'provider':'btproxy', 'service-classes':None,
                'service-id':None, 'profiles':None}
    append = False
    for i in lines:
        if append:
            if device.get('name',False): 
                services.append(device)
                device = {'host': target, 'description': 'btproxy',
                            'provider':'btproxy', 'service-classes':None,
                            'service-id':None, 'profiles':None}

                append = False
        if not i: 
            append = True
        else: 
            i = i.strip()
            if i.split(': ')[0] == 'Service Name':
                device['name'] = i.split(': ')[1]
            elif i.split(': ')[0] == 'Service Provider':
                device['provider'] = i.split(': ')[1]
            elif i.split(': ')[0] == 'UUID 128':
                device['service-id'] = i.split(': ')[1]
            elif i.split(': ')[0] == 'Channel':
                device['port'] = int(i.split(': ')[1])
                device['protocol'] = 'RFCOMM'
            elif i.split(': ')[0] == 'PSM':
                device['port'] = int(i.split(': ')[1])
                device['protocol'] = 'L2CAP'
    return services
    
            










