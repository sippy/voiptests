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

from .t2 import a_test2 as a_test_inv, b_test2 as b_test_inv

from sippy.CCEvents import CCEventTry, CCEventRing, CCEventFail, CCEventDisconnect

def cripple_body(self, sdp_body):
    sdp_body = sdp_body.getCopy()
    for sect in sdp_body.content.sections:
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        sect.c_header = None
        if sect.m_header.port + self.p_incr <= 0:
            self.p_incr = -self.p_incr
        sect.m_header.port += self.p_incr
        self.p_incr = -self.p_incr
    sdp_body.content.o_header.version += 1
    return sdp_body

class a_test_inv_brkn1(a_test_inv):
    cld = 'bob_inv_brkn1'
    cli = 'alice_inv_brkn1'
    name = f'{a_test_inv.name}: Bob screws response SDP'

    def alldone(self, ua):
        if self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done()

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventTry):
            return (super().recvEvent(event, ua))
        if isinstance(event, CCEventRing) and event.getData()[0] == 100:
            return (super().recvEvent(event, ua))
        if self.connect_done or not isinstance(event, (CCEventFail, CCEventDisconnect)):
            self.nerrs += 1
            raise ValueError(f'{self.failed_msg()}: INVITE has NOT failed with {event}')
        return (super().recvEvent(event, ua))

class b_test_inv_brkn1(b_test_inv):
    cli = a_test_inv_brkn1.cld
    name = a_test_inv_brkn1.name
    p_incr = -10

    def ring(self, ua):
        if self.connect_done or self.disconnect_done:
            return
        self.body = cripple_body(self, self.body)
        super().ring(ua)

    def alldone(self, ua):
        if self.ring_done and not self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        self.done()
