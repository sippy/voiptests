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

from test_cases.t1 import a_test1, b_test1

from sippy.Timeout import Timeout

class test_reinvite(object):
    reinvite = None
    ring_ival = 1.0
    answer_ival = 5.0
    disconnect_ival = 16.0

    def connected(self, ua):
        if self.reinvite != None:
            Timeout(self.reinvite, self.get_reinvite_ival(), 1, ua)

    def get_reinvite_ival(self):
        return self.disconnect_ival / 2.0

class a_test_reinvite(a_test1, test_reinvite):
    cld = 'bob_reinvite'
    cli = 'alice_reinvite'
    compact_sip = False

    def connected(self, ua, rtime, origin):
        test_reinvite.connected(self, ua)
        a_test1.connected(self, ua, rtime, origin)

    def alldone(self, ua):
        if not self.reinvite_done or not self.disconnect_done or self.nerrs > 0:
            if self.debug_lvl > -1:
                print '%s: subclass %s failed, acct=%s' % (self.my_name(), \
                  str(self.__class__), str(self.acct))
        else:
            self.rval = 0
        self.tccfg.done_cb(self)

class b_test_reinvite(b_test1, test_reinvite):
    cli = 'bob_reinvite'
    compact_sip = True

    def connected(self, ua, rtime, origin):
        test_reinvite.connected(self, ua)
        b_test1.connected(self, ua, rtime, origin)
