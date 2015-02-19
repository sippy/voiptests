from sippy.SipTransactionManager import SipTransactionManager
from sippy.Timeout import Timeout
from sippy.CCEvents import CCEventTry, CCEventDisconnect
from sippy.SipCallId import SipCallId
from sippy.SipCiscoGUID import SipCiscoGUID
from sippy.UA import UA
from twisted.internet import reactor

class a_test1(object):
    rval = 1
    connect_done = False
    disconnect_done = False

    def recvRequest(self, req):
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def recvEvent(self, event, ua):
        print 'Alice: Incoming event:', event

    def connected(self, ua, rtime, origin):
        Timeout(self.disconnect, 9, 1, ua)
        self.connect_done = True

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def disconnected(self, ua, rtime, origin, result = 0):
        if origin in ('switch', 'callee'):
            self.disconnect_done = True
        print 'Alice: disconnected', rtime, origin, result

    def alldone(self, ua):
        reactor.crash()
        if self.connect_done and self.disconnect_done:
            self.rval = 0

    def __init__(self, global_config, body):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        cld, cli = 'bob', 'alice'
        uaO = UA(global_config, event_cb = self.recvEvent, nh_address = ('127.0.0.1', 5060), \
          conn_cbs = (self.connected,), disc_cbs = (self.disconnected,), fail_cbs = (self.disconnected,), \
          dead_cbs = (self.alldone,))
        uaO.godead_timeout = 10

        event = CCEventTry((SipCallId(), SipCiscoGUID(), cli, cld, body, \
          None, 'Alice Smith'))
        uaO.recvEvent(event)
