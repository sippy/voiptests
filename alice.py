#!/usr/bin/env python2
#
# Copyright (c) 2015 Sippy Software, Inc. All rights reserved.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys, getopt
from time import sleep

sys.path.insert(0, 'dist/b2bua')

from sippy.MsgBody import MsgBody
from sippy.SipLogger import SipLogger
from sippy.SipConf import SipConf
from sippy.Core.EventDispatcher import ED2

from lib.PortRange import PortRange
from lib.test_config import test_config

body_txt = 'v=0\r\n' + \
  'o=- 380960 380960 IN IP4 192.168.22.95\r\n' + \
  's=-\r\n' + \
  'c=IN IP4 192.168.22.95\r\n' + \
  't=0 0\r\n' + \
  'm=audio 16474 RTP/AVP 18 0 2 4 8 96 97 98 101\r\n' + \
  'a=rtpmap:18 G729a/8000\r\n' + \
  'a=rtpmap:0 PCMU/8000\r\n' + \
  'a=rtpmap:2 G726-32/8000\r\n' + \
  'a=rtpmap:4 G723/8000\r\n' + \
  'a=rtpmap:8 PCMA/8000\r\n' + \
  'a=rtpmap:96 G726-40/8000\r\n' + \
  'a=rtpmap:97 G726-24/8000\r\n' + \
  'a=rtpmap:98 G726-16/8000\r\n' + \
  'a=rtpmap:101 telephone-event/8000\r\n' + \
  'a=fmtp:101 0-15\r\n' + \
  'a=ptime:30\r\n' + \
  'a=sendrecv\r\n'

if __name__ == '__main__':
    global_config = {}

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'Dp:t:l:P:T:46n:N:w:')
    except getopt.GetoptError:
        usage(global_config)

    tcfg = test_config(global_config)
    ttype = []
    pre_wait = None
    dry_run = False
    for o, a in opts:
        if o == '-p':
            tcfg.portrange = PortRange(a.strip())
            continue
        if o == '-t':
            if a != '*':
                tcfg.tests = tuple(['alice_' + x for x in a.split(',')])
            else:
                tcfg.tests = None
            continue
        if o == '-l':
            saddr = a.strip()
            if saddr == '*':
                saddr = SipConf.my_address
            global_config['_sip_address'] = saddr
            continue
        if o == '-P':
            global_config['_sip_port'] = int(a)
            continue
        if o == '-T':
            tcfg.test_timeout = int(a)
            continue
        if o == '-4':
            ttype.append('IP4')
            continue
        if o == '-6':
            ttype.append('IP6')
            continue
        if o == '-n':
            nh_address4 = a.split(':', 1)
            nh_address4[1] = int(nh_address4[1])
            tcfg.nh_address4 = tuple(nh_address4)
            continue
        if o == '-N':
            nh_address6 = a.rsplit(':', 1)
            nh_address6[1] = int(nh_address6[1])
            tcfg.nh_address6 = tuple(nh_address6)
            continue
        if o == '-w':
            pre_wait = float(a)
            continue
        if o == '-D':
            dry_run = True
            continue
    if len(ttype) > 0:
        tcfg.ttype = tuple(ttype)

    tcfg.body = MsgBody(body_txt)
    tcfg.body.parse()

    sl = SipLogger('alice_ua')
    global_config['_sip_logger'] = sl

    from a_test1 import a_test
    if pre_wait != None:
        sleep(pre_wait)
    acore = a_test(tcfg)

    if not dry_run:
        ED2.loop()

        sys.exit(acore.rval)
