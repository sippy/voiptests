# Copyright (c) 2015 Sippy Software, Inc. All rights reserved.
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

##import sys
##sys.path.insert(0, 'dist/b2bua')

from sippy.Time.Timeout import Timeout
from sippy.SipTransactionManager import SipTransactionManager
from sippy.Core.EventDispatcher import ED2
from random import random

from lib.test_config import fillhostport

from test_cases.t1 import b_test1, AuthRequired, AuthFailed
from test_cases.t2 import b_test2
from test_cases.t3 import b_test3
from test_cases.t4 import b_test4
from test_cases.t5 import b_test5
from test_cases.t6 import b_test6
from test_cases.t7 import b_test7
from test_cases.t8 import b_test8
from test_cases.t9 import b_test9
from test_cases.t10 import b_test10
from test_cases.t11 import b_test11
from test_cases.t12 import b_test12
from test_cases.t13 import b_test13
from test_cases.t14 import b_test14
from test_cases.early_cancel import b_test_early_cancel
from test_cases.early_cancel_lost100 import b_test_early_cancel_lost100
from test_cases.reinvite import b_test_reinvite
from test_cases.reinv_fail import b_test_reinv_fail
from test_cases.reinv_brkn1 import b_test_reinv_brkn1
from test_cases.reinv_brkn2 import b_test_reinv_brkn2
from test_cases.reinv_onhold import b_test_reinv_onhold
from test_cases.reinv_frombob import b_test_reinv_frombob
from test_cases.reinv_bad_ack import b_test_reinv_bad_ack

ALL_TESTS = (b_test1, b_test2, b_test3, b_test4, b_test5, b_test6, b_test7, \
  b_test8, b_test9, b_test10, b_test11, b_test12, b_test13, b_test14, \
  b_test_early_cancel, b_test_early_cancel_lost100, b_test_reinvite, \
  b_test_reinv_fail, b_test_reinv_brkn1, b_test_reinv_brkn2, \
  b_test_reinv_onhold, b_test_reinv_frombob, b_test_reinv_bad_ack)

class b_test(object):
    rval = 1
    nsubtests_running = 0
    tcfg = None

    def __init__(self, tcfg):
        tcfg.global_config['_sip_tm'] = SipTransactionManager(tcfg.global_config, self.recvRequest)
        Timeout(self.timeout, tcfg.test_timeout, 1)
        self.tcfg = tcfg

    def recvRequest(self, req, sip_t):
        if req.getHFBody('to').getTag() != None:
            # Request within dialog, but no such dialog
            return (req.genResponse(481, 'Call Leg/Transaction Does Not Exist'), None, None)
        if req.getMethod() == 'INVITE':
            # New dialog
            cld = req.getRURI().username
            for tclass in ALL_TESTS:
                if cld == tclass.cli:
                    break
            else:
                return (req.genResponse(404, 'Test Does Not Exist'), None, None)

            cli = req.getHFBody('from').getUrl().username
            if cli.endswith('_ipv6'):
                atype = 'IP6'
            else:
                atype = 'IP4'
            tccfg = self.tcfg.gen_tccfg(atype, self.subtest_done)

            subtest = tclass(tccfg)

            self.nsubtests_running += 1
            self.rval += 1
            sdp_body = self.tcfg.bodys[0 if random() < 0.5 else 1].getCopy()
            fillhostport(sdp_body, self.tcfg.portrange, tccfg.atype)
            try:
                return subtest.answer(self.tcfg.global_config, sdp_body, req, sip_t)
            except AuthRequired as ce:
                resp = req.genResponse(401, 'Unauthorized')
                resp.appendHeader(ce.challenge)
                self.nsubtests_running -= 1
                self.rval -= 1
                return (resp, None, None)
            except AuthFailed:
                resp = req.genResponse(403, 'Auth Failed')
                return (resp, None, None)
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def timeout(self):
        ED2.breakLoop()

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            if self.rval == 1:
                self.rval = 0
            ED2.breakLoop()
