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

from sippy.Core.EventDispatcher import ED2
from sippy.Math.recfilter import recfilter
from sippy.Time.Timeout import Timeout

from .sleep_abs_mono import sleep_abs_mono
from .spinor import spinor

class testcore_base(object):
    stm_class = None
    stats_name = 'Core'

    def __init__(self, tcfg):
        self.tcfg = tcfg
        if tcfg.pre_wait is not None:
            sleep_abs_mono(tcfg.pre_wait)

    def setup_stm(self, tcfg):
        if self.stm_class is None:
            raise RuntimeError('stm_class is not configured')
        self.stm_class.model_udp_server[1].nworkers = 1
        tcfg.global_config['_sip_tm'] = self.stm_class(tcfg.global_config, self.recvRequest)

    def setup_continuous_stats(self):
        self.spinor = spinor()
        self.rcf = recfilter(0.999, 1.0)
        self.update_stats()
        Timeout(self.idle_update, 1.0, -1)

    def recvRequest(self, req, sip_t):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def timeout(self):
        ED2.breakLoop()

    def update_stats(self):
        if self.nsubtests_running == 0:
            self.spinor.idle = True
        else:
            self.spinor.idle = False
        omsg = '\r%s: %d tests running %s, %f' % (self.stats_name, \
          self.nsubtests_running, self.spinor.tick(), self.rcf.lastval)
        sys.stdout.write(omsg)
        if len(omsg) < self.last_ulen:
            pad = ' ' * (self.last_ulen - len(omsg))
            sys.stdout.write(pad)
        sys.stdout.flush()
        self.last_ulen = len(omsg)

    def idle_update(self):
        if self.spinor.idle:
            self.update_stats()

    def _subtest_done_common(self, subtest):
        pass

    def _subtest_done_continuous(self, subtest):
        pass

    def _on_no_subtests_left(self):
        pass

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        self._subtest_done_common(subtest)
        if subtest.rval == 0:
            self.rval -= 1
        if self.tcfg.continuous:
            self._subtest_done_continuous(subtest)
            if subtest.rval == 0:
                self.rcf.apply(1.0)
            else:
                self.rcf.apply(0.0)
            self.update_stats()
        elif self.nsubtests_running == 0:
            self._on_no_subtests_left()
