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

from test_cases.t11 import a_test11
from test_cases.t2 import b_test2

# This tests verifies that settion half-setup no-media timeout (which is set
# to 45 seconds via -W45 option to the rtpproxy) is correctly executed and that
# media timeout is properly deliered to the B2B causing session to be
# disconnected.

class a_test12(a_test11):
    cld = 'bob_12'
    cli = 'alice_12'
    compact_sip = False

class b_test12(b_test2):
    cli = 'bob_12'
    compact_sip = True
    ring_ival = 55.0

    def alldone(self, ua):
        #print('b_test12.alldone', self.ring_done)
        if not self.ring_done and not self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            if self.debug_lvl > -1:
                print('%s: subclass %s failed' % (self.my_name(), str(self.__class__)))
        self.tccfg.done_cb(self)
