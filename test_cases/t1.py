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

from .TExceptions import SDPValidationFailure

from sippy.Time.Timeout import Timeout
from sippy.CCEvents import CCEventTry, CCEventDisconnect, CCEventConnect, \
  CCEventPreConnect, CCEventRing, CCEventFail
from sippy.SipCallId import SipCallId, gen_test_cid
from sippy.UA import UA
from sippy.SipFrom import gen_test_tag
from sippy.SipHeader import SipHeader
from sippy.SipWWWAuthenticate import SipWWWAuthenticate

from random import random

class AuthRequired(Exception):
    challenges = None

    def __init__(self, challenges):
        self.challenges = challenges
        Exception.__init__(self)

class AuthFailed(Exception):
    pass

class test(object):
    rval = 1
    nerrs = 0
    ring_done = False
    connect_done = False
    disconnect_done = False
    compact_sip = False
    tccfg = None
    debug_lvl = 0
    call_id = None
    godead_timeout = 10.0
    acct = None
    finfo_displayed = False

    def failed_msg(self):
        msg = '%s: subclass %s failed, call_id=%s, acct=%s' % (self.my_name(), \
          str(self.__class__), str(self.call_id), str(self.acct))
        return msg

    def alldone(self, ua):
        if self.ring_done and self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            if self.debug_lvl > -1 and not self.finfo_displayed:
                print(self.failed_msg())
                self.finfo_displayed = True
        self.tccfg.done_cb(self)

class a_test1(test):
    cld = 'bob_1'
    cli = 'alice_1'
    disconnect_ival = 9.0
    cancel_ival = None

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventRing) and not self.ring_done:
            self.ring_done = True
        if isinstance(event, CCEventRing) or isinstance(event, CCEventConnect) or \
          isinstance(event, CCEventPreConnect):
            code, reason, sdp_body = event.getData()
            if not (isinstance(event, CCEventRing) and sdp_body == None):
                sdp_body.parse()
                cres, why = self.tccfg.checkhostport(sdp_body)
                if not cres:
                    self.nerrs += 1
                    raise SDPValidationFailure('%s: SDP body has failed validation: %s:\n%s' %
                      (self.my_name(), why, str(sdp_body)))
        if self.debug_lvl > 0:
            print('%s: Incoming event: %s' % (self.my_name(), event))

    def connected(self, ua, rtime, origin):
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        self.connect_done = True

    def my_name(self):
        return 'Alice(%s)' % (self.cli,)

    def disconnect(self, ua):
        if self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def cancel(self, ua):
        if self.connect_done or self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'callee'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        if self.debug_lvl > 0:
            print('%s: disconnected' % self.my_name(), rtime, origin, result, self.acct)

    def __init__(self, tccfg):
        self.tccfg = tccfg
        if tccfg.cli != None:
            self.cli = tccfg.cli
        uaO = UA(tccfg.global_config, event_cb = self.recvEvent, nh_address = tccfg.nh_address, \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,), ltag = gen_test_tag())
        if tccfg.uac_creds != None:
            uaO.username = tccfg.uac_creds.username
            uaO.password = tccfg.uac_creds.password
            uaO.auth_enalgs = tccfg.uac_creds.enalgs

        uaO.godead_timeout = self.godead_timeout
        uaO.compact_sip = self.compact_sip
        self.call_id = SipCallId(body = gen_test_cid())
        event = CCEventTry((self.call_id, self.cli, self.cld, tccfg.body, \
          None, 'Alice Smith'))
        self.run(uaO, event)

    def run(self, ua, event):
        ua.recvEvent(event)
        if self.cancel_ival != None:
            Timeout(self.cancel, self.cancel_ival, 1, ua)

class b_test1(test):
    body = None
    atype = 'IP4'
    ring_ival = 5.0
    answer_ival = None
    disconnect_ival = None
    cli = 'bob_1'

    def __init__(self, tccfg):
        self.tccfg = tccfg
        if self.answer_ival == None:
            self.answer_ival = 9.0 + random() * 5.0
        if self.disconnect_ival == None:
            self.disconnect_ival = 5.0 + random() * 10.0

    def answer(self, global_config, body, req, sip_t):
        if self.connect_done or self.disconnect_done:
            return
        in_body = req.getBody()
        in_body.parse()
        cres, why = self.tccfg.checkhostport(in_body)
        if not cres:
            self.nerrs += 1
            raise SDPValidationFailure('%s: class %s: hostport validation has failed (%s): %s:\n%s' % \
              (self.my_name(), str(self.__class__), self.atype, why, in_body))
        if self.tccfg.uas_creds != None:
            if self.tccfg.uas_creds.realm != None:
                realm = self.tccfg.uas_creds.realm
            else:
                realm = req.getRURI().host
            if req.countHFs('authorization') == 0:
                challenges = []
                for alg in self.tccfg.uas_creds.enalgs:
                    cbody = SipWWWAuthenticate(algorithm = alg, realm = realm)
                    challenges.append(SipHeader(body = cbody))
                raise AuthRequired(challenges)
            sip_auth = req.getHFBody('authorization')
            if sip_auth.username != self.tccfg.uas_creds.username:
                raise AuthFailed()
            try:
                if not sip_auth.verify(self.tccfg.uas_creds.password, req.method):
                    raise AuthFailed()
            except ValueError:
                raise AuthFailed()
        # New dialog
        uaA = UA(global_config, self.recvEvent, disc_cbs = (self.disconnected,), \
          fail_cbs = (self.disconnected,), dead_cbs = (self.alldone,))
        uaA.godead_timeout = self.godead_timeout
        uaA.compact_sip = self.compact_sip
        Timeout(self.ring, self.ring_ival, 1, uaA)
        self.body = body
        self.call_id = req.getHFBody('call-id')
        return self.complete_answer(uaA, req, sip_t)

    def complete_answer(self, ua, req, sip_t):
        return ua.recvRequest(req, sip_t)

    def ring(self, ua):
        #print('%s: ring: %s %s' % (self.my_name(), self.cli, self.ring_done, self.disconnect_done))
        if self.connect_done or self.disconnect_done:
            return
        event = CCEventRing((180, 'Ringing', None), origin = 'switch')
        Timeout(self.connect, self.answer_ival, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

    def connect(self, ua):
        #if random() > 0.3:
        #    ua.recvEvent(CCEventFail((666, 'Random Failure')))
        #    return
        if self.connect_done or self.disconnect_done:
            return
        event = CCEventConnect((200, 'OK', self.body), origin = 'switch')
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        ua.recvEvent(event)
        self.connect_done = True

    def my_name(self):
        return 'Bob(%s)' % (self.cli,)

    def disconnect(self, ua):
        if self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def recvEvent(self, event, ua):
        if self.debug_lvl > 0:
            print('%s: Incoming event: %s' % (self.my_name(), str(event)))

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'caller'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        if self.debug_lvl > 0:
            print('%s: disconnected' % self.my_name(), rtime, origin, result, self.acct, self.ring_done)
