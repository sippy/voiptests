# Copyright (c) 2025 Sippy Software, Inc. All rights reserved.
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

from .reinv_frombob import a_test_reinv_frombob, b_test_reinv_frombob
from .TExceptions import ScenarioFailure

from sippy.SipAddress import SipAddress
from sippy.SipContact import SipContact
from sippy.SipURL import SipURL
from sippy.UA import UA


class _ReinviteTrackingUA(UA):
    """UA variant that keeps the R-URI of inbound in-dialog INVITEs."""

    def recvRequest(self, req, *args, **kwargs):
        if req.getMethod() == 'INVITE':
            self.last_in_dialog_invite_ruri = str(req.getRURI())
        return super(_ReinviteTrackingUA, self).recvRequest(req, *args, **kwargs)

class a_test_nated_contact(a_test_reinv_frombob):
    cld = 'bob_nated_contact'
    cli = 'alice_nated_contact'
    name = f'{a_test_reinv_frombob.name}: NATed Contact preserved on re-INVITE'
    compact_sip = False
    nat_contact_ip = '192.168.255.10'
    nat_contact_port = 5090

    def build_ua(self, tccfg):
        uaO = super(a_test_nated_contact, self).build_ua(tccfg, UA_class=_ReinviteTrackingUA)
        nat_contact = self._build_nat_contact()
        uaO.lContact = nat_contact
        self.expected_contact_uri = str(nat_contact.getUrl())
        return uaO

    def _build_nat_contact(self):
        nat_url = SipURL(username = self.cli, host = self.nat_contact_ip,
          port = self.nat_contact_port)
        nat_address = SipAddress(url = nat_url)
        return SipContact(address = nat_address)

    def on_reinvite_connected(self, ua):
        super(a_test_nated_contact, self).on_reinvite_connected(ua)
        ruri = getattr(ua, 'last_in_dialog_invite_ruri', None)
        if ruri != self.expected_contact_uri:
            self.nerrs += 1
            raise ScenarioFailure('%s: expected re-INVITE R-URI %s, got %s' %
              (self.failed_msg(), self.expected_contact_uri, ruri))

class b_test_nated_contact(b_test_reinv_frombob):
    cli = a_test_nated_contact.cld
    name = a_test_nated_contact.name
