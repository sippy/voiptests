#!/usr/local/bin/python

import sys
sys.path.insert(0, 'dist/b2bua')

from sippy.MsgBody import MsgBody
from sippy.SipLogger import SipLogger
from twisted.internet import reactor

body_txt = 'v=0\r\n' + \
  'o=- 380960 380960 IN IP4 192.168.22.95\r\n' + \
  's=-\r\n' + \
  'c=IN IP4 192.168.22.95\r\n' + \
  't=0 0\r\n' + \
  'm=audio 16474 RTP/AVP 18 0 2 4 8 96 97 98 101\r\n' + \
  'a=rtpmap:18 G729a/8000\r\n' + \
  'a=rtpmap:0 PCMU/8000\r\n' + \
  'a=rtpmap:2 G726-32/8000\r\n' + \
  'a=rtpmap:4 G723/8000\r\n' + \
  'a=rtpmap:8 PCMA/8000\r\n' + \
  'a=rtpmap:96 G726-40/8000\r\n' + \
  'a=rtpmap:97 G726-24/8000\r\n' + \
  'a=rtpmap:98 G726-16/8000\r\n' + \
  'a=rtpmap:101 telephone-event/8000\r\n' + \
  'a=fmtp:101 0-15\r\n' + \
  'a=ptime:30\r\n' + \
  'a=sendrecv\r\n'

if __name__ == '__main__':
    body = MsgBody(body_txt)

    global_config = {}

    global_config['_sip_address'] = sys.argv[1]
    global_config['_sip_port'] = int(sys.argv[2])
    global_config['_sip_logger'] = SipLogger('alice_ua')

    from a_test1 import a_test
    acore = a_test(global_config, body)

    reactor.run(installSignalHandlers = True)

    sys.exit(acore.rval)
