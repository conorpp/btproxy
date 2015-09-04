# Run this to MiTM SDP
# python sdpmitm_test.py <slave-bt-addr>

import sys
from btmitm_mitm import mitm_sdp

if __name__ == '__main__':
    mitm_sdp(sys.argv[1],sys.argv[2])
