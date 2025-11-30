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

import sys
from signal import SIGUSR1
##sys.path.insert(0, 'dist/b2bua')

from sippy.Time.Timeout import Timeout
from sippy.SipTransactionManager import SipTransactionManager
from sippy.Math.recfilter import recfilter
from sippy.Signal import Signal
from sippy.Core.EventDispatcher import ED2

from random import random

from .test_config import fillhostport
from .spinor import spinor

from ..test_cases.t1 import b_test1, AuthRequired, AuthFailed
from ..test_cases.t2 import b_test2
from ..test_cases.t3 import b_test3
from ..test_cases.t4 import b_test4
from ..test_cases.t5 import b_test5
from ..test_cases.t6 import b_test6
from ..test_cases.t7 import b_test7
from ..test_cases.t8 import b_test8
from ..test_cases.t9 import b_test9
from ..test_cases.t10 import b_test10
from ..test_cases.t11 import b_test11
from ..test_cases.t12 import b_test12
from ..test_cases.t13 import b_test13
from ..test_cases.t14 import b_test14
from ..test_cases.early_cancel import b_test_early_cancel
from ..test_cases.early_cancel_lost100 import b_test_early_cancel_lost100
from ..test_cases.reinvite import b_test_reinvite
from ..test_cases.reinv_fail import b_test_reinv_fail
from ..test_cases.reinv_brkn1 import b_test_reinv_brkn1
from ..test_cases.reinv_brkn2 import b_test_reinv_brkn2
from ..test_cases.reinv_onhold import b_test_reinv_onhold
from ..test_cases.reinv_adelay import b_test_reinv_adelay
from ..test_cases.reinv_frombob import b_test_reinv_frombob
from ..test_cases.reinv_bad_ack import b_test_reinv_bad_ack
from ..test_cases.inv_brkn1 import b_test_inv_brkn1
from ..test_cases.nated_contact import b_test_nated_contact

ALL_TESTS = (b_test1, b_test2, b_test3, b_test4, b_test5, b_test6, b_test7, \
  b_test8, b_test9, b_test10, b_test11, b_test12, b_test13, b_test14, \
  b_test_early_cancel, b_test_early_cancel_lost100, b_test_reinvite, \
  b_test_reinv_fail, b_test_reinv_brkn1, b_test_reinv_brkn2, \
  b_test_reinv_onhold, b_test_reinv_adelay, b_test_reinv_frombob, \
  b_test_reinv_bad_ack, b_test_inv_brkn1, b_test_nated_contact)

class STMHooks(object):
    lossemul = 0
    dupemul = None

from time import sleep

class BobSTM(SipTransactionManager):
    def spuriousDup(self, *args):
        SipTransactionManager.transmitData(self, *args)

    def transmitData(self, userv, data, address, cachesum = None, \
      lossemul = 0):
        if not isinstance(lossemul, STMHooks):
            return SipTransactionManager.transmitData(self, userv, data, address, \
              cachesum, lossemul)
        tdargs = (userv, data, address, cachesum, lossemul.lossemul)
        rval = SipTransactionManager.transmitData(self, *tdargs)
        if lossemul.dupemul is not None:
            if lossemul.dupemul < 0.01:
                sleep(lossemul.dupemul)
                SipTransactionManager.transmitData(self, *tdargs)
            else:
                Timeout(self.spuriousDup, lossemul.dupemul, 1, *tdargs)
        return rval

class b_test(object):
    rval = 1
    nsubtests_running = 0
    nsubtests_completed = 0
    tcfg = None
    debug = False
    spinor = None
    last_ulen = 0
    active_subtests = None

    def __init__(self, tcfg):
        tcfg.global_config['_sip_tm'] = BobSTM(tcfg.global_config, self.recvRequest)
        if not tcfg.continuous:
            Timeout(self.timeout, tcfg.test_timeout, 1)
        else:
            self.spinor = spinor()
            self.active_subtests = []
            self.rcf = recfilter(0.999, 1.0)
            self.update_stats()
            Timeout(self.idle_update, 1.0, -1)
            Signal(SIGUSR1, self.dumpcalls)
        self.tcfg = tcfg

    def dumpcalls(self):
        sys.stderr.write('BOB: Active tests:\n')
        for c in self.active_subtests:
            sys.stderr.write('\t%d %s\n' % (id(c), str(c)))
        sys.stderr.flush()

    def recvRequest(self, req, sip_t):
        if self.debug:
            print('recvRequest')
        if req.getHFBody('to').getTag() is not None:
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

            if self.tcfg.continuous:
                tclass.debug_lvl = -1
                tclass.godead_timeout = 1.0
            subtest = tclass(tccfg)

            sdp_body = self.tcfg.bodys[0 if random() < 0.5 else 1].getCopy()
            fillhostport(sdp_body, self.tcfg.portrange, tccfg.atype)
            try:
                rval = subtest.answer(self.tcfg.global_config, sdp_body, req, sip_t)
            except AuthRequired as ce:
                resp = req.genResponse(401, 'Unauthorized')
                resp.appendHeaders(ce.challenges)
                self.nsubtests_running -= 1
                self.rval -= 1
                resp.lossemul = STMHooks()
                resp.lossemul.dupemul = 0.001
                return (resp, None, None)
            except AuthFailed:
                resp = req.genResponse(403, 'Auth Failed')
                return (resp, None, None)

            self.nsubtests_running += 1
            if self.tcfg.continuous:
                self.active_subtests.append(subtest)
                self.update_stats()
            self.rval += 1
            return rval
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def timeout(self):
        ED2.breakLoop()

    def update_stats(self):
        if self.nsubtests_running == 0:
            self.spinor.idle = True
        else:
            self.spinor.idle = False
        omsg = '\rBob: %d tests running %s, %f' % (self.nsubtests_running, \
          self.spinor.tick(), self.rcf.lastval)
        sys.stdout.write(omsg)
        if len(omsg) < self.last_ulen:
            pad = ' ' * (self.last_ulen - len(omsg))
            sys.stdout.write(pad)
        sys.stdout.flush()
        self.last_ulen = len(omsg)

    def idle_update(self):
        if self.spinor.idle:
            self.update_stats()

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        if self.tcfg.continuous:
            self.active_subtests.remove(subtest)
        self.nsubtests_completed += 1
        if subtest.rval == 0:
            self.rval -= 1
        if self.tcfg.continuous:
            if subtest.rval == 0:
                self.rcf.apply(1.0)
            else:
                self.rcf.apply(0.0)
            self.update_stats()
        elif self.nsubtests_running == 0:
            if self.rval == 1:
                self.rval = 0
            ED2.breakLoop()
