# -*- test-case-name: fgdiag.disk.test_syslog -*-
# $Id$

"""Unit tests for syslog parsing."""

from twisted.trial import unittest

from fgdiag.disk import disk

irrelevant_messages = [
    "Feb 17 13:38:23 golden-test kernel: 3c59x: Donald Becker and others. www.scyld.com/network/vortex.html",
    ]

error_messages = [
    "Dec 27 16:46:16 progeny kernel: hdd: read_intr: status=0x59 { DriveReady SeekComplete DataRequest Error }",
    ]

class SyslogParsing(unittest.TestCase):
    """Test parsing of syslog messages."""

    def setUp(self):
        disk.startup_time = (0,) * 9

    def test_irrelevantMessage(self):
        """Filtering out non-disk messages."""
        for m in irrelevant_messages:
            result = disk.take_syslog_line(m)
            self.failUnlessEqual(result, None,
                                 "This message should have been ignored, "
                                 "but returned %s instead.\n%s" % (repr(result), m))

    def test_errorMessage(self):
        """Catching disk related errors."""
        for m in error_messages:
            result = disk.take_syslog_line(m)
            self.failUnless(result)

if __name__ == '__main__':
    unittest.main()
