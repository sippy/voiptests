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

from sippy.SipTransactionManager import SipTransactionManager
from sippy.Timeout import Timeout
from sippy.CCEvents import CCEventTry, CCEventDisconnect, CCEventConnect, \
  CCEventPreConnect, CCEventRing
from sippy.SipCallId import SipCallId
from sippy.SipCiscoGUID import SipCiscoGUID
from sippy.UA import UA
from sippy.SdpOrigin import SdpOrigin
from twisted.internet import reactor

from GenIPs import genIP

def fillhostport(sdp_body, portrange, atype = None):
    sdp_body.content.o_header = SdpOrigin()
    for i in range(0, len(sdp_body.content.sections)):
        sect = sdp_body.content.sections[i]
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        sect.m_header.port = portrange.gennotinrange()
        sect.c_header.atype, sect.c_header.addr = genIP(atype)

def checkhostport(sdp_body, portrange, atype):
    for i in range(0, len(sdp_body.content.sections)):
        sect = sdp_body.content.sections[i]
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        if not portrange.isinrange(sect.m_header.port):
            return False
        if atype == 'IP4' and sect.c_header.atype == 'IP4' and sect.c_header.addr == '127.0.0.1':
            continue
        if atype == 'IP6' and sect.c_header.atype == 'IP6' and sect.c_header.addr == '::1':
            continue
        return False
    return True

class a_test1(object):
    cld = 'bob_1'
    cli = 'alice_1'
    rval = 1
    nerrs = 0
    connect_done = False
    disconnect_done = False
    done_cb = None
    compact_sip = False
    atype = 'IP4'

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventRing) or isinstance(event, CCEventConnect) or \
          isinstance(event, CCEventPreConnect):
            code, reason, sdp_body = event.getData()
            if not (isinstance(event, CCEventRing) and sdp_body == None):
                sdp_body.parse()
                if not checkhostport(sdp_body, self.portrange, self.atype):
                    self.nerrs += 1
                    raise ValueError('Alice: SDP body has failed validation')
        print 'Alice: Incoming event:', event

    def connected(self, ua, rtime, origin):
        Timeout(self.disconnect, 9, 1, ua)
        self.connect_done = True

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'callee'):
            self.disconnect_done = True
        print 'Alice: disconnected', rtime, origin, result

    def alldone(self, ua):
        if self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done_cb(self)

    def __init__(self, global_config, body, done_cb, portrange):
        uaO = UA(global_config, event_cb = self.recvEvent, nh_address = ('127.0.0.1', 5060), \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,))
        uaO.godead_timeout = 10
        uaO.compact_sip = self.compact_sip

        event = CCEventTry((SipCallId(), SipCiscoGUID(), self.cli, self.cld, body, \
          None, 'Alice Smith'))
        uaO.recvEvent(event)
        self.done_cb = done_cb
        self.portrange = portrange

class a_test2(a_test1):
    cld = 'bob_2'
    cli = 'alice_2'
    atype = 'IP4'

class a_test3(a_test1):
    cld = 'bob_3'
    cli = 'alice_3'
    atype = 'IP4'

    def alldone(self, ua):
        if self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done_cb(self)

class a_test4(a_test3):
    cld = 'bob_4'
    cli = 'alice_4'
    atype = 'IP4'

class a_test5(a_test3):
    cld = 'bob_5'
    cli = 'alice_5'
    atype = 'IP4'

class a_test6(a_test1):
    cld = 'bob_6'
    cli = 'alice_6'
    compact_sip = True
    atype = 'IP4'

class a_test7(a_test2):
    cld = 'bob_7'
    cli = 'alice_7'
    compact_sip = True
    atype = 'IP4'

class a_test8(a_test3):
    cld = 'bob_8'
    cli = 'alice_8'
    compact_sip = True
    atype = 'IP4'

class a_test9(a_test4):
    cld = 'bob_9'
    cli = 'alice_9'
    compact_sip = True
    atype = 'IP4'

class a_test10(a_test5):
    cld = 'bob_10'
    cli = 'alice_10'
    compact_sip = True
    atype = 'IP4'

class a_test11(a_test1):
    cld = 'bob_11'
    cli = 'alice_11'
    compact_sip = True
    atype = 'IP4'

    def alldone(self, ua):
        if not self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done_cb(self)

class a_test12(a_test11):
    cld = 'bob_12'
    cli = 'alice_12'
    compact_sip = True
    atype = 'IP4'

class a_test13(a_test11):
    cld = 'bob_13'
    cli = 'alice_13'
    compact_sip = True
    atype = 'IP4'

ALL_TESTS = (a_test1, a_test2, a_test3, a_test4, a_test5, a_test6, a_test7, \
  a_test8, a_test9, a_test10, a_test11, a_test12, a_test13)

class a_test(object):
    nsubtests_running = 0
    rval = 1

    def __init__(self, global_config, body, portrange, tests, test_timeout):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        
        for subtest_class in ALL_TESTS:
            if subtest_class.cli not in tests:
                continue
            sdp_body = body.getCopy()
            fillhostport(sdp_body, portrange, subtest_class.atype)
            subtest = subtest_class(global_config, sdp_body, self.subtest_done, portrange)
            self.nsubtests_running += 1
        self.rval = self.nsubtests_running
        Timeout(self.timeout, test_timeout, 1)

    def recvRequest(self, req, sip_t):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            reactor.crash()

    def timeout(self):
        reactor.crash()
