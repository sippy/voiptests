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

from test_cases.reinvite import a_test_reinvite, b_test_reinvite

from sippy.CCEvents import CCEventRing, CCEventDisconnect, CCEventFail, \
  CCEventUpdate

class a_test_reinv_fail(a_test_reinvite):
    cld = 'bob_reinv_fail'
    cli = 'alice_reinv_fail'

    def recvEvent(self, event, ua):
        if self.reinvite_in_progress and not isinstance(event, CCEventRing):
            if not (isinstance(event, CCEventFail) or isinstance(event, CCEventDisconnect)):
                self.nerrs += 1
                raise ValueError('%s: re-INVITE has NOT failed' % (self.failed_msg(),))
            self.reinvite_in_progress = False
            self.reinvite_done = True
            if self.debug_lvl > 0:
                print('%s: Incoming event: %s, ignoring' % (self.my_name(), event))
            return
        return (a_test_reinvite.recvEvent(self, event, ua))

class b_test_reinv_fail(b_test_reinvite):
    cli = 'bob_reinv_fail'
    def recvEvent(self, event, ua):
        if not isinstance(event, CCEventUpdate):
            return (b_test_reinvite.recvEvent(self, event, ua))
        if self.debug_lvl > 0:
            print('Bob(%s): Incoming event: %s, generating failure' % (self.cli, str(event)))
        event = CCEventFail((408, 'Nobody is Home'))
        ua.recvEvent(event)
