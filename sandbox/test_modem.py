# $Id$

from twisted.trial import unittest
from twisted.trial.util import deferredResult
import newmodem as modem

MODEM_DEVICE="/dev/ttyS0"
TEST_TIMEOUT=20

class TestCallResponse(unittest.TestCase):
    def setUp(self):
        self.modem = modem.Modem(MODEM_DEVICE)

    def test_echo(self):
        d = self.modem.getResponse("AT\n")
        result = deferredResult(d, TEST_TIMEOUT)
        self.failUnlessEqual(result[:3], "AT\n")
