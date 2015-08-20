
import argparse,sys


parser = argparse.ArgumentParser(
                    description='Bluetooth MiTM Proxy'
                    )

parser.add_argument('addr_master', help='Bluetooth address of target master device', nargs='?',default=None)
parser.add_argument('addr_slave', help='Bluetooth address of target slave device', nargs='?',default=None)

parser.add_argument('-s','--scan', help='Scan for advertising Bluetooth devices', action='store_true')

parser.add_argument('-d','--detailed', help='Additionally lookup services when scanning', action='store_true')

parser.add_argument('-a','--set-address', help='Address to set for Bluetooth adaptor (requires -b)', )
parser.add_argument('-c','--set-class', help='Class to set for Bluetooth adaptor in hex, e.g. 0x89abde or 1234f6 (requires -b)', )
parser.add_argument('-n','--set-name', help='Name to set for Bluetooth adaptor (requires -b)', )

parser.add_argument('-b','--bluetooth', help='Select a Bluetooth adaptor', )
parser.add_argument('-l','--list', help='List Adaptors', action='store_true')

parser.add_argument('-k','--skip', help='Skip to connecting', action="store_true")
parser.add_argument('-1','--master-name', help='Spoofed name to use for master adaptor', default=None)
parser.add_argument('-2','--slave-name', help='Spoofed name to use for slave adaptor', default=None)
parser.add_argument('-C','--slave-active', help='Spoofed slave adaptor will actively connect to'+
                                                ' master device instead of listening for a connection', action='store_true')
parser.add_argument('-v','--verbose', help='Print additional info for debugging', action="store_true")
parser.add_argument('-z','--no-sdp', help='Let bluetoothd run SDP normally and let btmitm advertise copied services. (Not completed)', action="store_true")

args = parser.parse_args()
