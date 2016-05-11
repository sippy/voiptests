# Copyright (c) 2015-2016 Sippy Software, Inc. All rights reserved.
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

from sippy.Timeout import Timeout
from sippy.CCEvents import CCEventTry, CCEventDisconnect, CCEventConnect, \
  CCEventPreConnect, CCEventRing, CCEventUpdate, CCEventFail
from sippy.SipCallId import SipCallId
from sippy.SipCiscoGUID import SipCiscoGUID
from sippy.UA import UA

from random import random

def checkhostport(sdp_body, portrange, atype):
    for i in range(0, len(sdp_body.content.sections)):
        sect = sdp_body.content.sections[i]
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        if not portrange.isinrange(sect.m_header.port):
            return False
        if atype == 'IP4' and sect.c_header.atype == 'IP4' and sect.c_header.addr == '127.0.0.1':
            continue
        if atype == 'IP6' and sect.c_header.atype == 'IP6' and sect.c_header.addr in ('::1', '0:0:0:0:0:0:0:1'):
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
    disconnect_ival = 9.0
    cancel_ival = None
    reinvite_in_progress = False
    reinvite_done = False
    tccfg = None

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventRing) or isinstance(event, CCEventConnect) or \
          isinstance(event, CCEventPreConnect):
            code, reason, sdp_body = event.getData()
            if self.reinvite_in_progress and isinstance(event, CCEventConnect):
                self.reinvite_in_progress = False
                sdp_body.parse()
                if not self.tccfg.checkhostport(sdp_body):
                    self.nerrs += 1
                    raise ValueError('Alice: SDP body has failed validation')
                self.reinvite_done = True
            if not (isinstance(event, CCEventRing) and sdp_body == None):
                sdp_body.parse()
                if not self.tccfg.checkhostport(sdp_body):
                    self.nerrs += 1
                    raise ValueError('Alice: SDP body has failed validation')
        if self.reinvite_in_progress and (isinstance(event, CCEventDisconnect) or \
          isinstance(event, CCEventFail)):
            self.nerrs += 1
            raise ValueError('Alice: re-INVITE has failed')
        print '%s: Incoming event: %s' % (self.my_name(), event)

    def connected(self, ua, rtime, origin):
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        self.connect_done = True

    def reinvite(self, ua):
        if not self.connect_done or self.disconnect_done:
            return
        sdp_body = ua.lSDP.getCopy()
        sdp_body.content.o_header.version += 1
        for sect in sdp_body.content.sections:
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            sect.m_header.port += 10
            while 'sendrecv' in sect.a_headers:
                sect.a_headers.remove('sendrecv')
            sect += 'a=sendonly'
        event = CCEventUpdate(sdp_body, origin = 'switch')
        self.reinvite_in_progress = True
        ua.recvEvent(event)

    def my_name(self):
        return 'Alice(%s)' % (self.cli,)

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def cancel(self, ua):
        if self.connect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'callee'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        print '%s: disconnected' % self.my_name(), rtime, origin, result, self.acct

    def alldone(self, ua):
        if self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done_cb(self)

    def __init__(self, tccfg):
        self.tccfg = tccfg
        if tccfg.cli != None:
            self.cli = tccfg.cli
        uaO = UA(tccfg.global_config, event_cb = self.recvEvent, nh_address = tccfg.nh_address, \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,))
        uaO.godead_timeout = 10
        uaO.compact_sip = self.compact_sip
        event = CCEventTry((SipCallId(), SipCiscoGUID(), self.cli, self.cld, tccfg.body, \
          None, 'Alice Smith'))
        self.done_cb = tccfg.done_cb
        self.run(uaO, event)

    def run(self, ua, event):
        ua.recvEvent(event)
        if self.cancel_ival != None:
            Timeout(self.cancel, self.cancel_ival, 1, ua)

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
