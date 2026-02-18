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

from ctypes import CDLL, POINTER, Structure, byref, c_int, c_long
from errno import EINTR
from time import CLOCK_MONOTONIC, monotonic, sleep

_TIMER_ABSTIME = 1
_libc = CDLL(None)

class _timespec(Structure):
    _fields_ = [('tv_sec', c_long), ('tv_nsec', c_long)]

try:
    _clock_nanosleep = _libc.clock_nanosleep
    _clock_nanosleep.argtypes = (c_int, c_int, POINTER(_timespec), POINTER(_timespec))
    _clock_nanosleep.restype = c_int
except AttributeError as ex:
    from sys import platform as _sys_platform
    if any(_sys_platform.startswith(x) for x in ('freebsd', 'linux')):
        raise RuntimeError('cannot import clock_nanosleep()') from ex
    _clock_nanosleep = None

def sleep_abs_mono(deadline):
    if _clock_nanosleep is None:
        rem = deadline - monotonic()
        if rem <= 0:
            return
        sleep(rem)
        return
    sec = int(deadline)
    nsec = int((deadline - sec) * 1000000000.0)
    if nsec >= 1000000000:
        sec += 1
        nsec -= 1000000000
    rqtp = _timespec(sec, nsec)
    while True:
        err = _clock_nanosleep(CLOCK_MONOTONIC, _TIMER_ABSTIME, byref(rqtp), None)
        if err == 0:
            return
        if err == EINTR:
            # Preserve absolute deadline semantics across interrupts.
            continue
        raise OSError(err, 'clock_nanosleep() failed')
