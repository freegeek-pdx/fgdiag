"""Null Tester

Does nothing, but can be useful for framework diagnostics

"""

from lib import test, userinteraction
from lib.logging import create_node

# Create main log node
_log = create_node(__name__)

def null_scan():
    return (NullDevice(),)

class NullDevice(test.TestableDevice):

    # English name of the device tested
    name = "Null Device"

    def __init__(self):
        # Run inherited __init__
        test.TestableDevice.__init__(self)

    def _d_test(self):
        working = userinteraction.notice("Test being run")
        return test.status_from_boolean(True)

    def _d_data(self):
        working = userinteraction.notice("Data being retrieved")
        return {"notes":"Null tester output"}

    def _d_description(self, data):
        return "Null Tester"

class NullTester(test.GizmoTester):

    gizmotype = "Gizmo.Component"

    def scan(self):
        nulls = null_scan()
        for null in nulls:
            null.get_data()
        return nulls

    def run(self, nulls):
        for null in nulls:
            null.test()
        return nulls

    def destination(self, null):
        return test.Destination["Recycled"], "Please /dev/null the Null Device."

def main():
    from lib import testscript
    testscript.start(NullTester)
   
if __name__ == '__main__': main()
