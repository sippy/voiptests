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


class testcore_base(object):
    stm_class = None
    stats_name = 'Core'

    def setup_stm(self, tcfg):
        if self.stm_class is None:
            raise RuntimeError('stm_class is not configured')
        self.stm_class.model_udp_server[1].nworkers = 1
        tcfg.global_config['_sip_tm'] = self.stm_class(tcfg.global_config, self.recvRequest)

    def recvRequest(self, req, sip_t):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def timeout(self):
        ED2.breakLoop()

    def _subtest_done_common(self, subtest):
        pass

    def _on_no_subtests_left(self):
        pass

    def subtest_done(self, subtest):
        self.nsubtests_running -= 1
        self._subtest_done_common(subtest)
        if subtest.rval == 0:
            self.rval -= 1
        if self.nsubtests_running == 0:
            self._on_no_subtests_left()
            ED2.breakLoop()
