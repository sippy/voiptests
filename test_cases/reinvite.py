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

from .TExceptions import ScenarioFailure

from test_cases.t1 import a_test1, b_test1

from sippy.Time.Timeout import Timeout
from sippy.CCEvents import CCEventDisconnect, CCEventConnect, \
  CCEventUpdate, CCEventFail

class test_reinvite(object):
    reinvite_ival = None
    reinvite_in_progress = False
    reinvite_done = False
    nupdates = 0
    reinv_answ_delay = 0.0

    def connected(self, ua, *args):
        #print('test_reinvite.connected')
        rval = super(test_reinvite, self).connected(ua, *args)
        if self.reinvite_ival != None:
            Timeout(self.reinvite, self.reinvite_ival, 1, ua)
        return rval

    def complete_answer(self, ua, *args):
        rval = super(test_reinvite, self).complete_answer(ua, *args)
        if self.reinvite_ival != None:
            Timeout(self.reinvite, self.reinvite_ival, 1, ua)
        return rval

    def reinvite(self, ua, alter_port = True):
        if not self.connect_done or self.disconnect_done:
            return
        sdp_body = ua.lSDP.getCopy()
        sdp_body.content.o_header.version += 1
        if alter_port:
            for sect in sdp_body.content.sections:
                if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                    continue
                sect.m_header.port += 10
        event = CCEventUpdate(sdp_body, origin = 'switch')
        self.reinvite_in_progress = True
        ua.recvEvent(event)

    def get_reinvite_ival(self):
        return b_test_reinvite.disconnect_ival / 2.0

    def recvEvent(self, event, ua):
        #print('recvEvent')
        if isinstance(event, CCEventUpdate):
            self.process_reinvite(ua)
            self.nupdates += 1
            return
        if not self.reinvite_in_progress:
            return super(test_reinvite, self).recvEvent(event, ua)
        if isinstance(event, CCEventConnect):
            self.reinvite_in_progress = False
        elif (isinstance(event, CCEventDisconnect) or \
          isinstance(event, CCEventFail)):
            self.nerrs += 1
            raise ScenarioFailure('%s: re-INVITE has failed' % (self.failed_msg(),))
        rval = super(test_reinvite, self).recvEvent(event, ua)
        if isinstance(event, CCEventConnect):
            self.reinvite_done = True
            self.on_reinvite_connected(ua)
            #print('self.reinvite_done = True')
        return rval

    def on_reinvite_connected(self, ua):
        pass

    def process_reinvite(self, ua):
        if self.reinv_answ_delay > 0:
            Timeout(self._process_reinvite, self.reinv_answ_delay, 1, \
              ua)
            return
        self._process_reinvite(ua)

    def _process_reinvite(self, ua):
        sdp_body = ua.lSDP.getCopy()
        for sect in sdp_body.content.sections:
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            sect.m_header.port -= 10
        sdp_body.content.o_header.version += 1
        event = CCEventConnect((200, 'OK', sdp_body), origin = 'switch')
        ua.recvEvent(event)

    def alldone(self, ua):
        if self.reinvite_ival != None and \
          (not self.reinvite_done or not self.disconnect_done):
            self.nerrs += 1
        return super(test_reinvite, self).alldone(ua)

class a_test_reinvite(test_reinvite, a_test1):
    cld = 'bob_reinvite'
    cli = 'alice_reinvite'
    compact_sip = False

    def __init__(self, *args):
        self.reinvite_ival = self.get_reinvite_ival()
        a_test1.__init__(self, *args)

class b_test_reinvite(test_reinvite, b_test1):
    cli = a_test_reinvite.cld
    compact_sip = True
    ring_ival = 1.0
    answer_ival = 5.0
    disconnect_ival = 16
