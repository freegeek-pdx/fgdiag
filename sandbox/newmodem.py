# $Id$

from twisted.internet import defer
from twisted.internet import serialport

from twisted.protocols import basic
from twisted.python import log

class _ModemProtocol(basic.LineReceiver):
    response = None

    def lineReceived(self, data):
        if self.response:
            self.response.lineReceived(data)

    def setResponseTo(self, response):
        self.response = response


class _Response:
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
        return (_ModemProtocol.delimiter.join(self.lines)
                + _ModemProtocol.delimiter)

    def timedout(self):
        self.deferred.callback(self.read())

class Modem:
    device = None
    def __init__(self, device, reactor=None):
        self.proto = _ModemProtocol()
        if reactor is None:
            from twisted.internet import reactor as theReactor
            self.reactor = theReactor
        else:
            self.reactor = reactor
        self.device = serialport.SerialPort(self.proto, device, self.reactor)

    def getResponse(self, command):
        r = _Response(self.reactor)
        self.proto.setResponseTo(r)
        self.proto.sendLine(command)
        return r.deferred
