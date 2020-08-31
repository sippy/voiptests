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

from test_cases.t1 import a_test1, b_test1

class test_early_cancel(object):
    max_delay = 0.5

    def alldone(self, ua):
        if self.disconnect_done:
            duration, delay, connected, disconnected = self.acct
            if (duration, connected, disconnected) == (0, False, True) and \
              round(delay, 1) <= self.max_delay:
                self.rval = 0
            else:
                if self.debug_lvl > -1:
                    print(self.failed_msg())
                    self.finfo_displayed = True
        self.tccfg.done_cb(self)

class a_test_early_cancel(test_early_cancel, a_test1):
    cld = 'bob_early_cancel'
    cli = 'alice_early_cancel'
    compact_sip = False
    cancel_ival = 0.01

    def __init__(self, tccfg):
        tccfg.uac_creds = None
        test_early_cancel.__init__(self)
        a_test1.__init__(self, tccfg)

class b_test_early_cancel(test_early_cancel, b_test1):
    cli = 'bob_early_cancel'

    def __init__(self, tccfg):
        tccfg.uas_creds = None
        test_early_cancel.__init__(self)
        b_test1.__init__(self, tccfg)
