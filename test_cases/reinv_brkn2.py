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

from test_cases.reinv_fail import a_test_reinv_fail
from test_cases.reinvite import b_test_reinvite

class a_test_reinv_brkn2(a_test_reinv_fail):
    cld = 'bob_reinv_brkn2'
    cli = 'alice_reinv_brkn2'

    def reinvite(self, ua):
        if not self.connect_done or self.disconnect_done:
            return
        sdp_body_bak = ua.lSDP
        ua.lSDP = sdp_body_bak.getCopy()
        for sect in ua.lSDP.content.sections:
            sect.c_header = None
        rval = a_test_reinv_fail.reinvite(self, ua)
        ua.lSDP = sdp_body_bak
        return rval

class b_test_reinv_brkn2(b_test_reinvite):
    cli = 'bob_reinv_brkn2'
