# Copyright (c) 2016 Sippy Software, Inc. All rights reserved.
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

from random import random

from sippy.CCEvents import CCEventUpdate
from sippy.Time.Timeout import Timeout

from test_cases.reinvite import a_test_reinvite, b_test_reinvite

class a_test_reinv_onhold(a_test_reinvite):
    cld = 'bob_reinv_onhold'
    cli = 'alice_reinv_onhold'
    sched = None
    onhold_count = 0
    offhold_count = 0

    def __init__(self, *args, **kwargs):
        while True:
            self.sched = [0.1 + (random() * 0.5) for x in range(0, 4)]
            if sum(self.sched) < b_test_reinv_onhold.ring_ival + \
              b_test_reinv_onhold.answer_ival + self.get_reinvite_ival() - \
              self.disconnect_ival:
                break
        if self.debug_lvl > -1:
            print('%s: self.sched = %s' % (self.my_name(), self.sched))
        a_test_reinvite.__init__(self, *args, **kwargs)

    def reinvite(self, ua):
        if not self.connect_done or self.disconnect_done:
            return
        sdp_body_bak = ua.lSDP
        ua.lSDP = sdp_body_bak.getCopy()
        for sect in ua.lSDP.content.sections:
            if self.tccfg.atype == 'IP4':
                sect.c_header.addr = '0.0.0.0'
            else:
                sect.c_header.addr = '::'
            while 'sendrecv' in sect.a_headers:
                sect.a_headers.remove('sendrecv')
        rval = a_test_reinvite.reinvite(self, ua, alter_port = False)
        self.onhold_count += 1
        ua.lSDP = sdp_body_bak
        return rval

    def on_reinvite_connected(self, ua):
        if len(self.sched) > 0:
            if self.onhold_count > self.offhold_count:
                # Take call off-hold little bit later
                Timeout(self.off_hold, self.sched.pop(), 1, ua)
            else:
                Timeout(self.reinvite, self.sched.pop(), 1, ua)
        a_test_reinvite.on_reinvite_connected(self, ua)

    def off_hold(self, ua):
        a_test_reinvite.reinvite(self, ua, alter_port = False)
        self.offhold_count += 1

    def get_reinvite_ival(self):
        return a_test_reinvite.get_reinvite_ival(self) / 2.0

    def disconnect(self, ua):
        if self.disconnect_done:
            return
        if self.onhold_count != 3 or self.offhold_count != 2:
            Timeout(self.disconnect, 1.0, 1, ua)
            return
        a_test_reinvite.disconnect(self, ua)

class b_test_reinv_onhold(b_test_reinvite):
    cli = 'bob_reinv_onhold'
    onhold_count = 0
    offhold_count = 0

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventUpdate):
            sdp_body = event.getData()
            sdp_body.parse()
            onhold = False
            for sect in sdp_body.content.sections:
                onhold = sect.isOnHold()
            if onhold:
                self.onhold_count += 1
            else:
                self.offhold_count += 1
        return (b_test_reinvite.recvEvent(self, event, ua))

    def alldone(self, ua):
        if self.onhold_count != 3 or self.offhold_count != 2:
            if self.debug_lvl > -1:
                fmsg = self.failed_msg()
                print('%s: onhold_count = %d, offhold_count = %d' % \
                  (fmsg, self.onhold_count, self.offhold_count))
                self.finfo_displayed = True
            self.nerrs += 1
        return b_test_reinvite.alldone(self, ua)
