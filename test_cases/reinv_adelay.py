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

from sippy.Time.Timeout import Timeout

from time import sleep

class a_test_reinv_adelay(a_test_reinvite):
    cld = 'bob_reinv_adelay'
    cli = 'alice_reinv_adelay'

    def reinvite(self, ua, *args):
        a_test_reinvite.reinvite(self, ua, *args)
        #Timeout(self.gen_bye, b_test_reinv_adelay.reinv_answ_delay / 2, 1, ua)
        Timeout(self.disconnect, b_test_reinv_adelay.reinv_answ_delay / 2, 1, ua)

    def gen_bye(self, ua):
        req = ua.genRequest('BYE')
        ua.lCSeq += 1
        ua.global_config['_sip_tm'].newTransaction(req, \
          laddress = ua.source_address, compact = ua.compact_sip)
        sleep(0.001)
        self.gen_cancel(ua)
        #Timeout(self.gen_cancel, 0.01, 1, ua)

    def gen_cancel(self, ua):
        ua.global_config['_sip_tm'].cancelTransaction(ua.tr)

class b_test_reinv_adelay(b_test_reinvite):
    cli = a_test_reinv_adelay.cld
    reinv_answ_delay = 0.7
