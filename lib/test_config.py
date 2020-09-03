##import sys
##sys.path.insert(0, 'dist/b2bua')

from sippy.SdpOrigin import SdpOrigin

from lib.GenIPs import genIP
from lib.PortRange import PortRange

def fillhostport(sdp_body, portrange, atype = None):
    sdp_body.content.o_header = SdpOrigin()
    for i in range(0, len(sdp_body.content.sections)):
        sect = sdp_body.content.sections[i]
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        sect.m_header.port = portrange.gennotinrange()
        sect.c_header.atype, sect.c_header.addr = genIP(atype)

class AUTH_CREDS(object):
    username = None
    password = None
    enalgs = ('SHA-512-256', 'SHA-256', 'MD5')

    def __init__(self, username, password):
        self.username = username
        self.password = password

class test_case_config(object):
    global_config = None
    atype = None
    body = None
    done_cb = None
    portrange = None
    nh_address = None
    uas_creds = None
    uac_creds = None

    def checkhostport(self, sdp_body):
        for i in range(0, len(sdp_body.content.sections)):
            sect = sdp_body.content.sections[i]
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            if not self.portrange.isinrange(sect.m_header.port):
                return (False, 'not self.portrange.isinrange(%d)' % (sect.m_header.port,))
            if self.atype == 'IP4' and (sect.c_header.atype != 'IP4' or \
              sect.c_header.addr != self.nh_address[0]):
                 return (False, 'expected IPv4 address (%s)' % (self.nh_address[0],))
            if self.atype == 'IP6' and (sect.c_header.atype != 'IP6' or not \
              sect.c_header.addr in ('::1', '0:0:0:0:0:0:0:1')):
                return (False, 'expected IPv6 address %s or %s' % ('::1', '0:0:0:0:0:0:0:1',))
            continue
        return (True, 'all good')

class test_config(object):
    global_config = None
    ttype = ('IP4', 'IP6')
    body = None
    portrange = PortRange('12000-15000')
    tests = None
    test_timeout = 60
    nh_address4 = ('127.0.0.1', 5060)
    nh_address6 = ('[::1]', 5060)

    def gen_tccfg(self, atype, done_cb, cli = None):
        tccfg = test_case_config()
        tccfg.uac_creds = AUTH_CREDS('mightyuser', 's3cr3tpAssw0Rd')
        tccfg.uac_creds.enalgs = ('MD5',)
        tccfg.uas_creds = AUTH_CREDS('mightyuser', 's3cr3tpAssw0Rd')
        tccfg.global_config = self.global_config
        if self.body != None:
            tccfg.body = self.body.getCopy()
            fillhostport(tccfg.body, self.portrange, atype)
        tccfg.done_cb = done_cb
        tccfg.cli = cli
        tccfg.atype = atype
        if atype == 'IP4':
            tccfg.nh_address = self.nh_address4
        else:
            tccfg.nh_address = self.nh_address6
        tccfg.portrange = self.portrange
        return tccfg

    def __init__(self, global_config):
        self.global_config = global_config
