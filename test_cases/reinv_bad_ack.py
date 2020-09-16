# Copyright (c) 2018 Sippy Software, Inc. All rights reserved.
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
from test_cases.reinvite import test_reinvite

class a_test_reinv_bad_ack(test_reinvite, a_test1):
    cld = 'bob_reinv_bad_ack'
    cli = 'alice_reinv_bad_ack'
    compact_sip = False
    disconnect_ival = 50

    def __init__(self, *args):
        self.reinvite_ival = 1
        a_test1.__init__(self, *args)

    def reinvite(self, ua, alter_port = True):
        test_reinvite.reinvite(self, ua, alter_port)
        if not self.connect_done or self.disconnect_done:
            return
        ua.tr.uack = True

    def on_reinvite_connected(self, ua):
        ua.tr.ack.getHFBody('cseq').cseq = 0
        ua.global_config['_sip_tm'].sendACK(ua.tr)

    def disconnect(self, ua):
        if not self.disconnect_done:
            self.nerrs += 1
            # The ACK in the re-INVITE transaction is sent with wrong CSeq so
            # the call should have been interrupted early.
            raise ValueError('%s: The call was not interrupted early.' % self.my_name())
        a_test1.disconnect(self, ua)

class b_test_reinv_bad_ack(test_reinvite, b_test1):
    cli = a_test_reinv_bad_ack.cld
    compact_sip = True
    ring_ival = 1.0
    answer_ival = 5.0
    disconnect_ival = 60
