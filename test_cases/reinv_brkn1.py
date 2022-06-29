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

from test_cases.reinv_fail import a_test_reinv_fail, b_test_reinv_fail

from sippy.CCEvents import CCEventUpdate, CCEventConnect

class a_test_reinv_brkn1(a_test_reinv_fail):
    cld = 'bob_reinv_brkn1'
    cli = 'alice_reinv_brkn1'

class b_test_reinv_brkn1(b_test_reinv_fail):
    cli = 'bob_reinv_brkn1'
    p_incr = -10

    def recvEvent(self, event, ua):
        if not isinstance(event, CCEventUpdate):
            return (b_test_reinv_fail.recvEvent(self, event, ua))
        sdp_body = ua.lSDP.getCopy()
        for sect in sdp_body.content.sections:
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            sect.c_header = None
            if sect.m_header.port + self.p_incr <= 0:
                self.p_incr = -self.p_incr
            sect.m_header.port += self.p_incr
            self.p_incr = -self.p_incr
        sdp_body.content.o_header.version += 1
        event = CCEventConnect((200, 'OK', sdp_body), origin = 'switch')
        ua.recvEvent(event)
        self.nupdates += 1
