# $Id$

from twisted.internet import defer
from twisted.internet import serialport

from twisted.protocols import basic

import time

class ModemProtocol(basic.LineReceiver):
    response = None
    
    def lineReceived(self, data):
        # print repr(data)
        if self.response:
            response.lineReceived(data)

    def setResponseTo(self, response):
        self.response = response

class Response:
    timer = None
    timeoutSecs = 5.0

    def __init__(self, reactor):
        self.lines = []
        self.timer = reactor.callLater(self.timeoutSecs, self.timedout)
        self.deferred = defer.Deferred()

    def lineReceived(self, line):
        self.timer.reset(self.timeoutSecs)
        self.lines.append(line)

    def read(self):
        return ''.join(self.lines)

    def finished(self):
        self.timer.cancel()
        self.deferred.callback(self.read())

    def timedout(self):
        self.deferred.errback(FIXME)

class Modem:
    device = None
    def __init__(self, device):
        self.proto = ModemProtocol()
        from twisted.internet import reactor
        self.device = serialport.SerialPort(self.proto, device, reactor)

    def getResponse(self, command):
        r = Response()
        self.proto.sendLine("AT")
        self.proto.setResponseTo(r)
        return defer.Deferred()
        # return defer.succeed("AT\n")
