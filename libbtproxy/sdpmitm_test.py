#!/usr/bin/env python
# Run this to MiTM SDP

import sys
from mitm import mitm_sdp

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: ./sdpmitm_test.py <master-bt-addr> <slave-bt-addr>')
        sys.exit(1)
    mitm_sdp(sys.argv[1],sys.argv[2])
