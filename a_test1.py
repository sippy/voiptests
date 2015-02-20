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
from sippy.CCEvents import CCEventTry, CCEventDisconnect
from sippy.SipCallId import SipCallId
from sippy.SipCiscoGUID import SipCiscoGUID
from sippy.UA import UA
from twisted.internet import reactor

class a_test1(object):
    cld = 'bob_1'
    cli = 'alice_1'
    rval = 1
    connect_done = False
    disconnect_done = False
    done_cb = None

    def recvEvent(self, event, ua):
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
        if self.connect_done and self.disconnect_done:
            self.rval = 0
        self.done_cb(self)

    def __init__(self, global_config, body, done_cb):
        uaO = UA(global_config, event_cb = self.recvEvent, nh_address = ('127.0.0.1', 5060), \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,))
        uaO.godead_timeout = 10

        event = CCEventTry((SipCallId(), SipCiscoGUID(), self.cli, self.cld, body, \
          None, 'Alice Smith'))
        uaO.recvEvent(event)
        self.done_cb = done_cb

class a_test2(a_test1):
    cld = 'bob_2'
    cli = 'alice_2'

class a_test3(a_test1):
    cld = 'bob_3'
    cli = 'alice_3'

    def alldone(self, ua):
        if self.disconnect_done:
            self.rval = 0
        self.done_cb(self)

class a_test4(a_test3):
    cld = 'bob_4'
    cli = 'alice_4'

class a_test5(a_test3):
    cld = 'bob_5'
    cli = 'alice_5'

class a_test(object):
    nsubtests_running = 0
    rval = 1

    def __init__(self, global_config, body):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        
        for subtest_class in a_test1, a_test2, a_test3, a_test4, a_test5:
            subtest = subtest_class(global_config, body, self.subtest_done)
            self.nsubtests_running += 1
        self.rval = self.nsubtests_running
        Timeout(self.timeout, 45, 1)

    def recvRequest(self, req):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            reactor.crash()

    def timeout(self):
        reactor.crash()
