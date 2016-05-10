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

from sippy.UA import UA
from sippy.Timeout import Timeout
from sippy.CCEvents import CCEventRing, CCEventConnect, CCEventDisconnect, \
  CCEventFail, CCEventUpdate
from sippy.SipTransactionManager import SipTransactionManager
from twisted.internet import reactor
from random import random

from a_test1 import fillhostport, checkhostport

class b_test1(object):
    rval = 1
    nerrs = 0
    ring_done = False
    connect_done = False
    disconnect_done = False
    done_cb = None
    body = None
    compact_sip = False
    atype = 'IP4'
    ring_ival = 5.0
    answer_ival = None
    disconnect_ival = None
    cli = 'bob_1'
    acct = None
    nupdates = 0

    def __init__(self, done_cb, portrange):
        self.done_cb = done_cb
        self.portrange = portrange
        if self.answer_ival == None:
            self.answer_ival = 9.0 + random() * 5.0
        if self.disconnect_ival == None:
            self.disconnect_ival = 5.0 + random() * 10.0

    def answer(self, global_config, body, req, sip_t):
        in_body = req.getBody()
        in_body.parse()
        if not checkhostport(in_body, self.portrange, self.atype):
            self.nerrs += 1
            raise ValueError('Bob(%s): hostport validation has failed (%s):\n%s' % \
              (str(self.__class__), self.atype, in_body))
        # New dialog
        uaA = UA(global_config, self.recvEvent, disc_cbs = (self.disconnected,), \
          fail_cbs = (self.disconnected,), dead_cbs = (self.alldone,))
        uaA.godead_timeout = 10
        uaA.compact_sip = self.compact_sip
        Timeout(self.ring, self.ring_ival, 1, uaA)
        self.body = body
        return self.complete_answer(uaA, req, sip_t)

    def complete_answer(self, ua, req, sip_t):
        return ua.recvRequest(req, sip_t)

    def ring(self, ua):
        event = CCEventRing((180, 'Ringing', None), origin = 'switch')
        Timeout(self.connect, self.answer_ival, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

    def connect(self, ua):
        #if random() > 0.3:
        #    ua.recvEvent(CCEventFail((666, 'Random Failure')))
        #    return
        event = CCEventConnect((200, 'OK', self.body), origin = 'switch')
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        ua.recvEvent(event)
        self.connect_done = True

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def recvEvent(self, event, ua):
        print 'Bob(%s): Incoming event: %s' % (self.cli, str(event))
        if isinstance(event, CCEventUpdate):
            sdp_body = ua.lSDP.getCopy()
            for sect in sdp_body.content.sections:
                if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                    continue
                sect.m_header.port -= 10
            sdp_body.content.o_header.version += 1
            event = CCEventConnect((200, 'OK', sdp_body), origin = 'switch')
            ua.recvEvent(event)
            self.nupdates += 1

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'caller'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        print 'Bob(%s): disconnected' % self.cli, rtime, origin, result, self.acct

    def alldone(self, ua):
        if self.ring_done and self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            print 'Bob(%s): subclass %s failed' % (self.cli, str(self.__class__))
        self.done_cb(self)

class b_test2(b_test1):
    cli = 'bob_2'

    def ring(self, ua):
        event = CCEventRing((183, 'Session Progress', self.body), \
          origin = 'switch')
        Timeout(self.connect, self.answer_ival, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

class b_test3(b_test1):
    cli = 'bob_3'

    def connect(self, ua):
        event = CCEventFail((501, 'Post-ring Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.connect_done = True

class b_test4(b_test1):
    cli = 'bob_4'

    def ring(self, ua):
        event = CCEventFail((502, 'Pre-ring Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.ring_done = True
        self.connect_done = True

class b_test5(b_test2):
    cli = 'bob_5'

    def connect(self, ua):
        event = CCEventFail((503, 'Post-early-session Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.connect_done = True

class b_test6(b_test1):
    cli = 'bob_6'
    compact_sip = True

class b_test7(b_test2):
    cli = 'bob_7'
    compact_sip = True

class b_test8(b_test3):
    cli = 'bob_8'
    compact_sip = True

class b_test9(b_test4):
    cli = 'bob_9'
    compact_sip = True

class b_test10(b_test5):
    cli = 'bob_10'
    compact_sip = True

class b_test11(b_test1):
    cli = 'bob_11'
    compact_sip = True
    answer_ival = 55.0

    def alldone(self, ua):
        if self.ring_done and not self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            print 'Bob(%s): subclass %s failed' % (self.cli, str(self.__class__))
        self.done_cb(self)

class b_test12(b_test2):
    cli = 'bob_12'
    compact_sip = True
    ring_ival = 55.0

    def alldone(self, ua):
        if self.ring_done and not self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            print 'Bob(%s): subclass %s failed' % (self.cli, str(self.__class__))
        self.done_cb(self)

class b_test13(b_test12):
    cli = 'bob_13'
    compact_sip = True
    ring_ival = 1.0
    answer_ival = 70.0

class b_test14(b_test1):
    cli = 'bob_14'
    compact_sip = True
    ring_ival = 1.0
    answer_ival = 2.0
    disconnect_ival = 120

class b_test_early_cancel(b_test1):
    cli = 'bob_early_cancel'
    max_delay = 0.5

    def alldone(self, ua):
        if self.disconnect_done:
            duration, delay, connected, disconnected = self.acct
            if (duration, connected, disconnected) == (0, False, True) and \
              delay < self.max_delay:
                self.rval = 0
            else:
                print 'Bob(%s): subclass %s failed, acct=%s' % (self.cli, str(self.__class__), str(self.acct))
        self.done_cb(self)

class b_test_early_cancel_lost100(b_test_early_cancel):
    cli = 'bob_early_cancel_lost100'
    max_delay = 1.0

    def complete_answer(self, ua, req, sip_t):
        ua.uas_lossemul = 1
        return b_test1.complete_answer(self, ua, req, sip_t)

class b_test_reinvite(b_test1):
    cli = 'bob_reinvite'
    compact_sip = True
    ring_ival = 1.0
    answer_ival = 5.0
    disconnect_ival = 16

class b_test_reinv_fail(b_test_reinvite):
    cli = 'bob_reinv_fail'
    def recvEvent(self, event, ua):
        if not isinstance(event, CCEventUpdate):
            return (b_test_reinvite.recvEvent(self, event, ua))
        print 'Bob(%s): Incoming event: %s, generating failure' % (self.cli, str(event))
        event = CCEventFail((408, 'Nobody is Home'))
        ua.recvEvent(event)

class b_test_reinv_brkn1(b_test_reinv_fail):
    cli = 'bob_reinv_brkn1'

    def recvEvent(self, event, ua):
        if not isinstance(event, CCEventUpdate):
            return (b_test_reinvite.recvEvent(self, event, ua))
        sdp_body = ua.lSDP.getCopy()
        for sect in sdp_body.content.sections:
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            sect.c_header = None
            sect.m_header.port -= 10
        sdp_body.content.o_header.version += 1
        event = CCEventConnect((200, 'OK', sdp_body), origin = 'switch')
        ua.recvEvent(event)
        self.nupdates += 1

class b_test_reinv_brkn2(b_test_reinvite):
    cli = 'bob_reinv_brkn2'

ALL_TESTS = (b_test1, b_test2, b_test3, b_test4, b_test5, b_test6, b_test7, \
  b_test8, b_test9, b_test10, b_test11, b_test12, b_test13, b_test14, \
  b_test_early_cancel, b_test_early_cancel_lost100, b_test_reinvite, \
  b_test_reinv_fail, b_test_reinv_brkn1, b_test_reinv_brkn2)

class b_test(object):
    rval = 1
    bodys = None
    global_config = None
    nsubtests_running = 0
    portrange = None

    def __init__(self, global_config, bodys, portrange, test_timeout):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        Timeout(self.timeout, test_timeout, 1)
        self.bodys = bodys
        self.global_config = global_config
        self.portrange = portrange

    def recvRequest(self, req, sip_t):
        if req.getHFBody('to').getTag() != None:
            # Request within dialog, but no such dialog
            return (req.genResponse(481, 'Call Leg/Transaction Does Not Exist'), None, None)
        if req.getMethod() == 'INVITE':
            # New dialog
            cld = req.getRURI().username
            for tclass in ALL_TESTS:
                if cld == tclass.cli:
                    break
            else:
                return (req.genResponse(404, 'Test Does Not Exist'), None, None)
            subtest = tclass(self.subtest_done, self.portrange)
            cli = req.getHFBody('from').getUrl().username
            if cli.endswith('_ipv6'):
                subtest.atype = 'IP6'
            self.nsubtests_running += 1
            self.rval += 1
            sdp_body = self.bodys[0 if random() < 0.5 else 1].getCopy()
            fillhostport(sdp_body, self.portrange, subtest.atype)
            return subtest.answer(self.global_config, sdp_body, req, sip_t)
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def timeout(self):
        reactor.crash()

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            if self.rval == 1:
                self.rval = 0
            reactor.crash()
