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
sys.path.insert(0, 'dist/b2bua')
sys.path.insert(0, 'lib')

from sippy.MsgBody import MsgBody
from sippy.SipLogger import SipLogger
from twisted.internet import reactor

from PortRange import PortRange

body_audio = 'v=0\r\n' + \
    'o=987654382 4650 4650 IN IP4 192.168.0.90\r\n' + \
    's=BobPentiumIV Call\r\n' + \
    'c=IN IP4 192.168.0.5\r\n' + \
    't=0 0\r\n' + \
    'm=audio 20000 RTP/AVP 0 4 8 101\r\n' + \
    'a=rtpmap:0 PCMU/8000/1\r\n' + \
    'a=rtpmap:4 G723/8000/1\r\n' + \
    'a=rtpmap:8 PCMA/8000/1\r\n' + \
    'a=rtpmap:101 telephone-event/8000\r\n' + \
    'a=fmtp:101 0-15\r\n'
body_fax = 'v=0\r\n' + \
    'o=BOBSDP 187392 187393 IN IP4 192.168.174.156\r\n' + \
    's=BOBSDP Session\r\n' + \
    'c=IN IP4 192.168.174.156\r\n' + \
    't=0 0\r\n' + \
    'm=image 53278 udptl t38\r\n' + \
    'a=T38FaxVersion:0\r\n' + \
    'a=T38MaxBitRate:14400\r\n' + \
    'a=T38FaxRateManagement:transferredTCF\r\n' + \
    'a=T38FaxMaxBuffer:262\r\n' + \
    'a=T38FaxMaxDatagram:176\r\n' + \
    'a=T38FaxUdpEC:t38UDPRedundancy\r\n'

BODIES_ALL = (body_audio, body_fax)

if __name__ == '__main__':
    global_config = {}

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:l:P:T:')
    except getopt.GetoptError:
        usage(global_config)
    portrange = PortRange('12000-15000')
    for o, a in opts:
        if o == '-p':
            portrange = PortRange(a.strip())
            continue
        if o == '-l':
            global_config['_sip_address'] = a.strip()
            continue
        if o == '-P':
            global_config['_sip_port'] = int(a)
            continue
        if o == '-T':
            test_timeout = int(a)
            continue

    bodys = [MsgBody(x) for x in BODIES_ALL]
    for body in bodys:
        body.parse()

    sl = SipLogger('bob_ua')
    global_config['_sip_logger'] = sl

    from b_test1 import b_test
    bcore = b_test(global_config, tuple(bodys), portrange, test_timeout)

    reactor.run(installSignalHandlers = True)
    sys.exit(bcore.rval)
