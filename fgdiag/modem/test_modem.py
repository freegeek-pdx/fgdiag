#!/usr/bin/env python
# $Id$

"""Unit tests for modem testing."""

from fgdiag.modem import modem
from twisted.trial import unittest
import string

COMMAND_SET = {
    'ATI0\n': ["256k EPROM"],
    'ATI1\n': ["Somethingorother 33.6"],
    }

class ModemStub:
    error_response = ["ERROR"]
    command_set = COMMAND_SET

    def __init__(self, command_set=None):
        if command_set is not None:
            self.command_set = command_set

    def write(self, data):
        data = string.upper(data)
        if not data[:2] == "AT":
            return
        self._line = 0
        if self.command_set.has_key(data):
            self._response = self.command_set[data]
        else:
            self._response = self.error_response

    def readline(self):
        if self._line < len(self._response):
            response = self._response[self._line] + '\n'
            self._line += 1
            return response
        else:
            return ''

class ResponseParser(unittest.TestCase):
    def test_needsAmoreDescriptiveName(self):
        my_modem = ModemStub()
        results = modem.find_speed(my_modem)
        self.failUnless(results)
        self.failUnlessEqual(len(results), 1, "Too many canidate responses: %s" % (results,))
        self.failUnlessEqual(results[0][0], '336')

if __name__ == '__main__':
    unittest.main()
