from fgdiag.lib import test
from twisted.trial import unittest

def test_scan():
    # Creates two Devices, one working, one not.
    return TestDevice(True), TestDevice(False)

class TestDevice(test.TestableDevice):

    # English name of the device tested
    name = "Gizmo Thingy"

    def __init__(self, working):
        self.working = working
        test.TestableDevice.__init__(self)

    def _d_test(self):
        return test.status_from_boolean(self.working)

    def _d_data(self):
        return {"notes":"Data"}

    def _d_description(self, data):
        return "Special Gizmo Thingy"

class TestTester(unittest.TestCase):
    def test_statusfrombool(self):
        """Check that status constants are sane"""
        self.assertEqual(test.status_from_boolean(True), test.Status["Passed"])
        self.assertEqual(test.status_from_boolean(False), test.Status["Failed"])

    def test_testdevice(self):
        """Make sure testabledevice is working completely"""
        scanresults = test_scan()
        self.failUnless(scanresults)
        for device in scanresults:
            # Test data
            data = device.get_data()
            self.failUnless(data)
            self.assertEqual(data, {"notes":"Data"})
            self.failUnlessEqual(data, device.data)

            # Test Description
            self.failUnless(device.description)
            self.assertEqual(device.description, "Special Gizmo Thingy")

            # Test test
            status = device.test()
            self.failIfEqual(status, test.Status["Unknown"])
            self.assertEqual(status, test.status_from_boolean(device.working))
            self.failUnlessEqual(status, device.status)

if __name__ == '__main__':
    unittest.main()
