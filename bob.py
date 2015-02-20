#!/usr/local/bin/python

import sys
sys.path.insert(0, 'dist/b2bua')

from sippy.MsgBody import MsgBody
from sippy.SipLogger import SipLogger
from twisted.internet import reactor

body_txt = 'v=0\r\n' + \
    'o=987654382 4650 4650 IN IP4 192.168.0.90\r\n' + \
    's=ATA186 Call\r\n' + \
    'c=IN IP4 192.168.0.5\r\n' + \
    't=0 0\r\n' + \
    'm=audio 20000 RTP/AVP 0 4 8 101\r\n' + \
    'a=rtpmap:0 PCMU/8000/1\r\n' + \
    'a=rtpmap:4 G723/8000/1\r\n' + \
    'a=rtpmap:8 PCMA/8000/1\r\n' + \
    'a=rtpmap:101 telephone-event/8000\r\n' + \
    'a=fmtp:101 0-15\r\n'

if __name__ == '__main__':
    body = MsgBody(body_txt)

    global_config = {}

    global_config['_sip_address'] = sys.argv[1]
    global_config['_sip_port'] = int(sys.argv[2])
    global_config['_sip_logger'] = SipLogger('bob_ua')

    from b_test1 import b_test
    bcore = b_test(global_config, body)

    reactor.run(installSignalHandlers = True)
    sys.exit(bcore.rval)
