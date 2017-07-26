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

from sippy.SipTransactionManager import SipTransactionManager
from sippy.Timeout import Timeout
from twisted.internet import reactor
from random import shuffle

from test_cases.t1 import a_test1
from test_cases.t2 import a_test2
from test_cases.t3 import a_test3
from test_cases.t4 import a_test4
from test_cases.t5 import a_test5
from test_cases.t6 import a_test6
from test_cases.t7 import a_test7
from test_cases.t8 import a_test8
from test_cases.t9 import a_test9
from test_cases.t10 import a_test10
from test_cases.t11 import a_test11
from test_cases.t12 import a_test12
from test_cases.t13 import a_test13
from test_cases.t14 import a_test14
from test_cases.early_cancel import a_test_early_cancel
from test_cases.early_cancel_lost100 import a_test_early_cancel_lost100
from test_cases.reinvite import a_test_reinvite
from test_cases.reinv_fail import a_test_reinv_fail
from test_cases.reinv_brkn1 import a_test_reinv_brkn1
from test_cases.reinv_brkn2 import a_test_reinv_brkn2
from test_cases.reinv_onhold import a_test_reinv_onhold
from test_cases.reinv_frombob import a_test_reinv_frombob

ALL_TESTS = (a_test1, a_test2, a_test3, a_test4, a_test5, a_test6, a_test7, \
  a_test8, a_test9, a_test10, a_test11, a_test12, a_test13, a_test14, \
  a_test_early_cancel, a_test_early_cancel_lost100, a_test_reinvite, \
  a_test_reinv_fail, a_test_reinv_brkn1, a_test_reinv_brkn2, \
  a_test_reinv_onhold, a_test_reinv_frombob)

class a_test(object):
    nsubtests_running = 0
    rval = 1

    def __init__(self, tcfg):
        tcfg.global_config['_sip_tm'] = SipTransactionManager(tcfg.global_config, self.recvRequest)

        i = 0
        ttype = tcfg.ttype
        if len(ttype) == 1:
            ttype += ttype
        atests = ALL_TESTS * len(ttype)
        for subtest_class in atests:
            if tcfg.tests != None and subtest_class.cli not in tcfg.tests:
                subtest_class.disabled = True
                i += 1
                continue
            subtest_class.disabled = False
            cli = subtest_class.cli
            if i >= len(ALL_TESTS):
                atype = ttype[1]
            else:
                atype = ttype[0]
            cli += '_ipv%s' % atype[-1]
            subtest_class._tccfg = tcfg.gen_tccfg(atype, self.subtest_done, cli)
            print 'tcfg.gen_tccfg(%s, self.subtest_done, %s)' % (atype, cli)
            i += 1
        atests = list(atests)
        shuffle(atests)
        for subtest_class in atests:
            if subtest_class.disabled:
                continue
            subtest = subtest_class(subtest_class._tccfg)
            self.nsubtests_running += 1
        self.rval = self.nsubtests_running
        Timeout(self.timeout, tcfg.test_timeout, 1)

    def recvRequest(self, req, sip_t):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            reactor.crash()

    def timeout(self):
        reactor.crash()
