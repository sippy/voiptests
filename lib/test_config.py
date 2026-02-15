##import sys
##sys.path.insert(0, 'dist/b2bua')

from importlib.util import spec_from_file_location, module_from_spec
import os

from sippy.SdpOrigin import SdpOrigin
from sippy.SdpGeneric import SdpGeneric

from .GenIPs import genIP
from .PortRange import PortRange

SIPPY_RTP_OUSER = 'SippyRTP'

def fillhostport(sdp_body, portrange, atype, signalling_only):
    sdp_body.content.o_header = SdpOrigin()
    if not signalling_only:
        sdp_body.content.s_header = SdpGeneric(SIPPY_RTP_OUSER)
    for i in range(0, len(sdp_body.content.sections)):
        sect = sdp_body.content.sections[i]
        if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
            continue
        sect.m_header.port = portrange.gennotinrange()
        sect.c_header.atype, sect.c_header.addr = genIP(atype)

class AUTH_CREDS(object):
    username = None
    password = None
    realm = None
    enalgs = ('SHA-512-256-sess', 'SHA-256-sess', 'MD5-sess', None)

    def __init__(self, username, password):
        self.username = username
        self.password = password

def load_cfg(side):
    try:
        scn  = os.environ['MM_AUTH']
    except KeyError as ex:
        raise ImportError('MM_AUTH is not set') from ex
    module_name = side + '_cfg'
    module_path = 'scenarios/' + scn + '/' + module_name + '.py'
    spec = spec_from_file_location(module_name, module_path)
    emsg = f'Could not find module {module_name} in {module_path}'
    if spec is None: raise ImportError(emsg)
    m = module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except FileNotFoundError as ex:
        raise ImportError(emsg) from ex
    return m

class test_case_config(object):
    global_config = None
    atype = None
    body = None
    done_cb = None
    portrange = None
    nh_address = None
    uas_creds = None
    uac_creds = None
    check_media_ips = None
    cli = None
    signalling_only = False

    def __init__(self, nh_address):
        self.nh_address = nh_address
        ename = 'NH_MEDIA_IPS'
        if ename in os.environ:
            #print(os.environ)
            self.check_media_ips = os.environ[ename].split(',')
            #sys.exit(1)
        else:
            self.check_media_ips = (self.nh_address[0],)

    def checkhostport(self, sdp_body):
        for i in range(0, len(sdp_body.content.sections)):
            sect = sdp_body.content.sections[i]
            if sect.m_header.transport.lower() not in ('udp', 'udptl', 'rtp/avp'):
                continue
            if not self.portrange.isinrange(sect.m_header.port):
                return (False, 'not self.portrange.isinrange(%d)' % (sect.m_header.port,))
            if self.atype == 'IP4' and (sect.c_header.atype != 'IP4' or \
              sect.c_header.addr not in self.check_media_ips) and '*' not in self.check_media_ips:
                 return (False, 'expected IPv4 address (%s)' % (self.check_media_ips,))
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
    acfg = None
    bcfg = None
    tests_mightfail = tuple()
    signalling_only = False

    def gen_tccfg(self, atype, signalling_only, done_cb, cli=None):
        if atype == 'IP4':
            nh_address = self.nh_address4
        else:
            nh_address = self.nh_address6
        tccfg = test_case_config(nh_address)
        if self.acfg != None:
            tccfg.uac_creds = self.acfg.AUTH_CREDS()
        if self.bcfg != None:
            tccfg.uas_creds = self.bcfg.AUTH_CREDS()
        tccfg.global_config = self.global_config
        if self.body != None:
            tccfg.body = self.body.getCopy()
            fillhostport(tccfg.body, self.portrange, atype, signalling_only)
        tccfg.done_cb = done_cb
        tccfg.cli = cli
        tccfg.atype = atype
        tccfg.portrange = self.portrange
        tccfg.signalling_only = signalling_only
        return tccfg

    def __init__(self, global_config):
        self.global_config = global_config
        try:
            self.acfg = load_cfg('alice')
        except ImportError:
            pass
        try:
            self.bcfg = load_cfg('bob')
        except ImportError:
            pass
