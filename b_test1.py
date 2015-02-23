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
  CCEventFail
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

    def __init__(self, done_cb, portrange):
        self.done_cb = done_cb
        self.portrange = portrange

    def answer(self, global_config, body, req):
        in_body = req.getBody()
        in_body.parse()
        if not checkhostport(in_body, self.portrange):
            self.nerrs += 1
            raise ValueError('Bob: hostport validation has failed')
        # New dialog
        uaA = UA(global_config, self.recvEvent, disc_cbs = (self.disconnected,), \
          fail_cbs = (self.disconnected,), dead_cbs = (self.alldone,))
        uaA.godead_timeout = 10
        Timeout(self.ring, 5, 1, uaA)
        self.body = body
        return uaA.recvRequest(req)

    def ring(self, ua):
        event = CCEventRing((180, 'Ringing', None), origin = 'switch')
        Timeout(self.connect, 9.0 + random() * 5.0, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

    def connect(self, ua):
        #if random() > 0.3:
        #    ua.recvEvent(CCEventFail((666, 'Random Failure')))
        #    return
        event = CCEventConnect((200, 'OK', self.body), origin = 'switch')
        Timeout(self.disconnect, 5.0 + random() * 10.0, 1, ua)
        ua.recvEvent(event)
        self.connect_done = True

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def recvEvent(self, event, ua):
        print 'Bob: Incoming event:', event

    def disconnected(self, ua, rtime, origin, result = 0):
        print 'Bob: disconnected', rtime, origin, result
        if origin in ('switch', 'caller'):
            self.disconnect_done = True

    def alldone(self, ua):
        if self.ring_done and self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            print 'Bob: subclass %s failed' % str(self.__class__)
        self.done_cb(self)

class b_test2(b_test1):
    def ring(self, ua):
        event = CCEventRing((183, 'Session Progress', self.body), \
          origin = 'switch')
        Timeout(self.connect, 9.0 + random() * 5.0, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

class b_test3(b_test1):
    def connect(self, ua):
        event = CCEventFail((501, 'Post-ring Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.connect_done = True

class b_test4(b_test1):
    def ring(self, ua):
        event = CCEventFail((502, 'Pre-ring Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.ring_done = True
        self.connect_done = True

class b_test5(b_test2):
    def connect(self, ua):
        event = CCEventFail((503, 'Post-early-session Failure'), \
          origin = 'switch')
        ua.recvEvent(event)
        self.connect_done = True

class b_test(object):
    rval = 1
    body = None
    global_config = None
    nsubtests_running = 0
    portrange = None

    def __init__(self, global_config, body, portrange):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        Timeout(self.timeout, 45, 1)
        self.body = body
        self.global_config = global_config
        self.portrange = portrange

    def recvRequest(self, req):
        if req.getHFBody('to').getTag() != None:
            # Request within dialog, but no such dialog
            return (req.genResponse(481, 'Call Leg/Transaction Does Not Exist'), None, None)
        if req.getMethod() == 'INVITE':
            # New dialog
            cld = req.getRURI().username
            if cld == 'bob_1':
                subtest = b_test1(self.subtest_done, self.portrange)
            elif cld == 'bob_2':
                subtest = b_test2(self.subtest_done, self.portrange)
            elif cld == 'bob_3':
                subtest = b_test3(self.subtest_done, self.portrange)
            elif cld == 'bob_4':
                subtest = b_test4(self.subtest_done, self.portrange)
            elif cld == 'bob_5':
                subtest = b_test5(self.subtest_done, self.portrange)
            else:
                return (req.genResponse(404, 'Test Does Not Exist'), None, None)
            self.nsubtests_running += 1
            self.rval += 1
            sdp_body = self.body.getCopy()
            fillhostport(sdp_body, self.portrange)
            return subtest.answer(self.global_config, sdp_body, req)
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
