from sippy.UA import UA
from sippy.Timeout import Timeout
from sippy.CCEvents import CCEventRing, CCEventConnect, CCEventDisconnect
from sippy.SipTransactionManager import SipTransactionManager
from twisted.internet import reactor
from random import random

class b_test1(object):
    rval = 1
    body = None
    global_config = None
    ring_done = False
    connect_done = False
    disconnect_done = False

    def __init__(self, global_config, body):
        global_config['_sip_tm'] = SipTransactionManager(global_config, self.recvRequest)
        Timeout(self.alldone, 45, 1, None)
        self.body = body
        self.global_config = global_config

    def recvRequest(self, req):
        if req.getHFBody('to').getTag() != None:
            # Request within dialog, but no such dialog
            return (req.genResponse(481, 'Call Leg/Transaction Does Not Exist'), None, None)
        if req.getMethod() == 'INVITE':
            # New dialog
            uaA = UA(self.global_config, self.recvEvent, disc_cbs = (self.disconnected,), \
              fail_cbs = (self.disconnected,), dead_cbs = (self.alldone,))
            uaA.godead_timeout = 10
            Timeout(self.ring, 5, 1, uaA)
            return uaA.recvRequest(req)
        return (req.genResponse(501, 'Not Implemented'), None, None)

    def ring(self, ua):
        event = CCEventRing((180, 'Ringing', None), origin = 'switch')
        Timeout(self.connect, 9.0 + random() * 5.0, 1, ua)
        ua.recvEvent(event)
        self.ring_done = True

    def connect(self, ua):
        #if random() > 0.3:
        #    ua.recvEvent(CCEventFail((666, 'Random Failure')))
        #    return
        event = CCEventConnect((200, 'OK', self.body), origin = 'switch')
        Timeout(self.disconnect, 5.0 + random() * 10.0, 1, ua)
        ua.recvEvent(event)
        self.connect_done = True

    def disconnect(self, ua):
        event = CCEventDisconnect(origin = 'switch')
        ua.recvEvent(event)

    def recvEvent(self, event, ua):
        print 'Bob: Incoming event:', event

    def disconnected(self, ua, rtime, origin, result = 0):
        print 'Bob: disconnected', rtime, origin, result
        if origin in ('switch', 'caller'):
            self.disconnect_done = True

    def alldone(self, ua):
        reactor.crash()
        if self.ring_done and self.connect_done and self.disconnect_done:
            self.rval = 0
