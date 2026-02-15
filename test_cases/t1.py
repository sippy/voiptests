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

from .TExceptions import SDPValidationFailure

from sippy.Time.Timeout import Timeout
from sippy.CCEvents import CCEventTry, CCEventDisconnect, CCEventConnect, \
  CCEventPreConnect, CCEventRing, CCEventFail
from sippy.SipCallId import SipCallId, gen_test_cid
from sippy.UA import UA
from sippy.SipFrom import gen_test_tag
from sippy.SipHeader import SipHeader
from sippy.SipWWWAuthenticate import SipWWWAuthenticate
from sippy.misc import local4remote

from array import array
from threading import Lock
from random import random, randint
from socket import AF_INET, AF_INET6

from sippy.Rtp.Core.AudioChunk import AudioChunk
from sippy.Rtp.EPoint import RTPEPoint
from sippy.Rtp.Params import RTPParams
from sippy.Rtp.Conf import RTPConf
from sippy.Rtp.OutputWorker import RTPOutputWorker
from sippy.Rtp.Handlers import RTPHandlers
from sippy.Rtp.Codecs.G711 import G711Codec
from sippy.Rtp.Codecs.G722 import G722Codec

class FeedingOutputWorker(RTPOutputWorker):
    def __init__(self, rtp_params, owner):
        self._on_drain = owner._rtp_feed_once
        super().__init__(rtp_params)

    def update_frm_ctrs(self, rcvd_inc = 0, prcsd_inc = 0):
        #print('update_frm_ctrs', self)
        res = super().update_frm_ctrs(rcvd_inc, prcsd_inc)
        if res[0] == res[1]:
            self._on_drain(self.soundout)
        return res

class AuthRequired(Exception):
    challenges = None

    def __init__(self, challenges):
        self.challenges = challenges
        super().__init__()

class AuthFailed(Exception):
    pass

class test(object):
    rval = 1
    nerrs = 0
    ring_done = False
    connect_done = False
    disconnect_done = False
    compact_sip = False
    tccfg = None
    debug_lvl = 0
    call_id = None
    godead_timeout = 10.0
    acct = None
    finfo_displayed = False
    mightfail = False
    _done_called = False
    _rtp_inited = False
    rtp_chunk_ms = 100
    rtp_audio_sr = 8000

    def failed_msg(self):
        msg = '%s: subclass %s failed, call_id=%s, acct=%s' % (self.my_name(), \
          str(self.__class__), str(self.call_id), str(self.acct))
        return msg

    def _rtp_init(self):
        assert not self._rtp_inited
        self._rtp_inited = True
        self._done_called = False
        self._rtp_enabled = not self.tccfg.signalling_only
        self._rtp_lock = Lock()
        self._rtp_ep = None
        self._rtp_closing = False
        self._rtp_tx_gen = 0
        self._rtp_tx_chunks = 0
        self._rtp_rx_frames = 0
        self._rtp_target = None
        self._rtp_codec = None
        self._rtp_ptime = None
        self._rtp_updates = 0
        self._rtp_error = None
        self._rtp_tx_chunk = None

    def _rtp_pick_media(self, sdp_body):
        assert sdp_body is not None
        sdp_body.parse()
        for sect in sdp_body.content.sections:
            if sect.m_header.stype.lower() != 'audio':
                continue
            if sect.m_header.transport.lower() not in ('udp', 'rtp/avp'):
                continue
            if 0 in sect.m_header.formats:
                codec = G711Codec
            elif 9 in sect.m_header.formats:
                codec = G722Codec
            else:
                continue
            ptime = 20
            for ah in sect.a_headers:
                if ah.name != 'ptime' or ah.value is None:
                    continue
                try:
                    ptime = max(10, int(ah.value))
                except ValueError:
                    pass
                break
            rtp_proto = sect.c_header.atype
            return ((sect.c_header.addr, sect.m_header.port), codec, ptime, rtp_proto)
        return None

    def _rtp_audio_in(self, chunk):
        with self._rtp_lock:
            self._rtp_rx_frames += chunk.nframes

    def _rtp_feed_once(self, rtp_soundout):
        if self._rtp_closing:
            return
        if self._rtp_tx_chunk is None:
            nframes = max(1, self.rtp_audio_sr * self.rtp_chunk_ms // 1000)
            self._rtp_tx_chunk = AudioChunk(array('h', (randint(-32768, 32767) for _ in range(nframes))), \
              self.rtp_audio_sr)
        achunk = self._rtp_tx_chunk
        try:
            rtp_soundout(achunk)
        except Exception as ex:
            self._rtp_error = str(ex)
            return
        with self._rtp_lock:
            self._rtp_tx_gen += achunk.nframes
            self._rtp_tx_chunks += 1

    def _rtp_start_or_update(self, sdp_body):
        assert self._rtp_inited
        if not self._rtp_enabled:
            return
        mdata = self._rtp_pick_media(sdp_body)
        if mdata is None:
            return
        rtp_target, codec, ptime, rtp_proto = mdata
        params = RTPParams(rtp_target, out_ptime = ptime, out_sr = self.rtp_audio_sr, \
          rtp_proto = rtp_proto)
        params.codec = codec
        if self._rtp_ep is None:
            handlers = RTPHandlers()
            handlers.writer_cls = lambda rtp_params: FeedingOutputWorker(rtp_params, self)
            self._rtp_ep = RTPEPoint(RTPConf(), params, self._rtp_audio_in, handlers = handlers)
        else:
            self._rtp_ep.update(params)
            self._rtp_updates += 1
        self._rtp_target = rtp_target
        self._rtp_codec = codec.__name__
        self._rtp_ptime = ptime

    def _rtp_prepare_local_sdp(self, sdp_body, laddr=None, af=None):
        assert self._rtp_inited
        if not self._rtp_enabled:
            return
        mdata = self._rtp_pick_media(sdp_body)
        assert mdata is not None
        _rtp_target, codec, ptime, rtp_proto = mdata
        if af is not None:
            rtp_proto = 'IP4' if af == AF_INET else 'IP6'
        if self._rtp_ep is None:
            params = RTPParams(None, out_ptime = ptime, out_sr = self.rtp_audio_sr, \
              rtp_proto = rtp_proto)
            params.codec = codec
            handlers = RTPHandlers()
            handlers.writer_cls = lambda rtp_params: FeedingOutputWorker(rtp_params, self)
            self._rtp_ep = RTPEPoint(RTPConf(), params, self._rtp_audio_in, handlers = handlers)
        rp = self._rtp_ep.rtp_params
        _laddr, lport = rp.rtp_laddr, rp.rtp_lport
        if laddr is None:
            laddr = _laddr
        assert laddr not in ('0.0.0.0', '::', None, '*', '')
        assert not laddr.startswith('[') and not laddr.endswith(']')
        self._rtp_apply_local_media(sdp_body, laddr, lport, rtp_proto)

    def _rtp_apply_local_media(self, sdp_body, laddr, lport, rtp_proto):
        sdp_body.parse()
        for sect in sdp_body.content.sections:
            if sect.m_header.stype.lower() != 'audio':
                continue
            if sect.m_header.transport.lower() not in ('udp', 'rtp/avp'):
                continue
            sect.m_header.port = lport
            if None not in (laddr, sect.c_header):
                sect.c_header.addr = laddr
                sect.c_header.atype = rtp_proto
            return

    def _rtp_shutdown_stats(self):
        assert self._rtp_inited
        if not self._rtp_enabled:
            return {'tx_rcvd' : 0, 'tx_prcsd' : 0, 'rx_pkts' : 0}
        assert not self._rtp_closing
        self._rtp_closing = True
        stats = {'tx_rcvd' : 0, 'tx_prcsd' : 0, 'rx_pkts' : 0}
        if self._rtp_ep is None:
            return stats
        try:
            if self._rtp_ep.writer is not None:
                tx_rcvd, tx_prcsd = self._rtp_ep.writer.get_frm_ctrs()
                stats['tx_rcvd'] = tx_rcvd
                stats['tx_prcsd'] = tx_prcsd
            if self._rtp_ep.rsess is not None:
                stats['rx_pkts'] = self._rtp_ep.rsess.npkts
            self._rtp_ep.shutdown()
        except Exception as ex:
            self._rtp_error = str(ex)
        finally:
            self._rtp_ep = None
        return stats

    def report_rtp(self):
        assert self._rtp_inited
        stats = self._rtp_shutdown_stats()
        if self._rtp_error is not None and self.debug_lvl > -1:
            print('%s: RTP error: %s' % (self.my_name(), self._rtp_error))
        if self._rtp_target is None:
            print('%s: RTP stats: no session' % self.my_name())
            return
        smsg = '%s: RTP stats: target=%s:%d codec=%s ptime=%d tx_gen=%d tx_chunks=%d tx_rcvd=%d tx_prcsd=%d rx_frames=%d rx_pkts=%d updates=%d'
        args = (self.my_name(), self._rtp_target[0], self._rtp_target[1], self._rtp_codec, \
          self._rtp_ptime, self._rtp_tx_gen, self._rtp_tx_chunks, stats['tx_rcvd'], \
          stats['tx_prcsd'], self._rtp_rx_frames, stats['rx_pkts'], self._rtp_updates)
        print(smsg % args)

    def done(self):
        assert self._rtp_inited
        assert not self._done_called
        self._done_called = True
        if not self.tccfg.signalling_only:
            self.report_rtp()
        self.tccfg.done_cb(self)

    def alldone(self, ua):
        if self.ring_done and self.connect_done and self.disconnect_done and self.nerrs == 0:
            self.rval = 0
        else:
            if self.debug_lvl > -1 and not self.finfo_displayed:
                fmsg = self.failed_msg()
                if self.mightfail:
                    fmsg = f'{fmsg} [IGNORED]'
                print(fmsg)
                self.finfo_displayed = True
            if self.mightfail:
                self.rval = 0
        self.done()

class a_test1(test):
    cld = 'bob_1'
    cli = 'alice_1'
    name = 'Basic test #1'
    disconnect_ival = 9.0
    cancel_ival = None

    def recvEvent(self, event, ua):
        if isinstance(event, CCEventRing) and not self.ring_done:
            self.ring_done = True
        if isinstance(event, CCEventRing) or isinstance(event, CCEventConnect) or \
          isinstance(event, CCEventPreConnect):
            code, reason, sdp_body = event.getData()
            if not (isinstance(event, CCEventRing) and sdp_body == None):
                sdp_body.parse()
                cres, why = self.tccfg.checkhostport(sdp_body)
                if not cres:
                    self.nerrs += 1
                    raise SDPValidationFailure('%s: SDP body has failed validation: %s:\n%s' %
                      (self.my_name(), why, str(sdp_body)))
                self._rtp_start_or_update(sdp_body)
        if self.debug_lvl > 0:
            print('%s: Incoming event: %s' % (self.my_name(), event))

    def connected(self, ua, rtime, origin):
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        self.connect_done = True

    def my_name(self):
        return 'Alice(%s)' % (self.cli,)

    def disconnect(self, ua):
        if self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def cancel(self, ua):
        if self.connect_done or self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'callee'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        if self.debug_lvl > 0:
            print('%s: disconnected' % self.my_name(), rtime, origin, result, self.acct)

    def __init__(self, tccfg):
        self.tccfg = tccfg
        self._rtp_init()
        body = tccfg.body
        if self._rtp_enabled:
            body = body.getCopy()
            nh_host = tccfg.nh_address[0]
            if nh_host.startswith('[') and nh_host.endswith(']'):
                af = AF_INET6
                nh_host = nh_host[1:-1]
            else:
                af = AF_INET
            rtp_laddr = local4remote(nh_host, family=af)
            if af == AF_INET6 and rtp_laddr.startswith('[') and rtp_laddr.endswith(']'):
                rtp_laddr = rtp_laddr[1:-1]
            self._rtp_prepare_local_sdp(body, rtp_laddr, af)
        if tccfg.cli != None:
            self.cli = tccfg.cli
        uaO = self.build_ua(tccfg)
        self.call_id = SipCallId(body = gen_test_cid())
        event = CCEventTry((self.call_id, self.cli, self.cld, body, \
          None, 'Alice Smith'))
        self.run(uaO, event)

    def build_ua(self, tccfg, UA_class = UA):
        uaO = UA_class(tccfg.global_config, event_cb = self.recvEvent, nh_address = tccfg.nh_address, \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,), ltag = gen_test_tag())
        if tccfg.uac_creds != None:
            uaO.username = tccfg.uac_creds.username
            uaO.password = tccfg.uac_creds.password
            uaO.auth_enalgs = tccfg.uac_creds.enalgs

        uaO.godead_timeout = self.godead_timeout
        uaO.compact_sip = self.compact_sip
        return uaO

    def run(self, ua, event):
        ua.recvEvent(event)
        if self.cancel_ival != None:
            Timeout(self.cancel, self.cancel_ival, 1, ua)

class b_test1(test):
    body = None
    atype = 'IP4'
    ring_ival = 5.0
    answer_ival = None
    disconnect_ival = None
    cli = a_test1.cld
    name = a_test1.name

    def __init__(self, tccfg):
        self.tccfg = tccfg
        self._rtp_init()
        if self.answer_ival == None:
            self.answer_ival = 9.0 + random() * 5.0
        if self.disconnect_ival == None:
            self.disconnect_ival = 5.0 + random() * 10.0

    def answer(self, global_config, body, req, sip_t):
        if self.connect_done or self.disconnect_done:
            return
        in_body = req.getBody()
        in_body.parse()
        cres, why = self.tccfg.checkhostport(in_body)
        if not cres:
            self.nerrs += 1
            raise SDPValidationFailure('%s: class %s: hostport validation has failed (%s): %s:\n%s' % \
              (self.my_name(), str(self.__class__), self.atype, why, in_body))
        if self.tccfg.uas_creds != None:
            if self.tccfg.uas_creds.realm != None:
                realm = self.tccfg.uas_creds.realm
            else:
                realm = req.getRURI().host
            if req.countHFs('authorization') == 0:
                challenges = []
                for alg in self.tccfg.uas_creds.enalgs:
                    cbody = SipWWWAuthenticate(algorithm = alg, realm = realm)
                    challenges.append(SipHeader(body = cbody))
                raise AuthRequired(challenges)
            sip_auth = req.getHFBody('authorization')
            if sip_auth.username != self.tccfg.uas_creds.username:
                raise AuthFailed()
            try:
                if not sip_auth.verify(self.tccfg.uas_creds.password, req.method):
                    raise AuthFailed()
            except ValueError:
                raise AuthFailed()
        assert self._rtp_inited
        # New dialog
        uaA = UA(global_config, self.recvEvent, disc_cbs = (self.disconnected,), \
          fail_cbs = (self.disconnected,), dead_cbs = (self.alldone,))
        uaA.godead_timeout = self.godead_timeout
        uaA.compact_sip = self.compact_sip
        Timeout(self.ring, self.ring_ival, 1, uaA)
        self.body = body
        self.call_id = req.getHFBody('call-id')
        return self.complete_answer(uaA, req, sip_t)

    def complete_answer(self, ua, req, sip_t):
        return ua.recvRequest(req, sip_t)

    def ring(self, ua):
        #print('%s: ring: %s %s' % (self.my_name(), self.cli, self.ring_done, self.disconnect_done))
        if self.connect_done or self.disconnect_done:
            return
        event = CCEventRing((180, 'Ringing', None), origin = 'switch')
        Timeout(self.connect, self.answer_ival, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

    def _make_media_answer(self, sdp):
        body = self.body
        assert sdp is not None
        if self._rtp_enabled:
            body = body.getCopy()
            self._rtp_start_or_update(sdp)
            rp = self._rtp_ep.rtp_params
            laddr, lport = rp.rtp_laddr, rp.rtp_lport
            rtp_proto = rp.rtp_proto
            self._rtp_apply_local_media(body, laddr, lport, rtp_proto)
        return body

    def connect(self, ua):
        #if random() > 0.3:
        #    ua.recvEvent(CCEventFail((666, 'Random Failure')))
        #    return
        if self.connect_done or self.disconnect_done:
            return
        body = self._make_media_answer(ua.rSDP)
        event = CCEventConnect((200, 'OK', body), origin = 'switch')
        Timeout(self.disconnect, self.disconnect_ival, 1, ua)
        ua.recvEvent(event)
        self.connect_done = True

    def my_name(self):
        return 'Bob(%s)' % (self.cli,)

    def disconnect(self, ua):
        if self.disconnect_done:
            return
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def recvEvent(self, event, ua):
        if self.debug_lvl > 0:
            print('%s: Incoming event: %s' % (self.my_name(), str(event)))

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'caller'):
            self.disconnect_done = True
        self.acct = ua.getAcct()
        if self.debug_lvl > 0:
            print('%s: disconnected' % self.my_name(), rtime, origin, result, self.acct, self.ring_done)
