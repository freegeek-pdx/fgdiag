"""Testing API Tester

Runs through some functions of the testing api.

"""

import commands
from lib import test, userinteraction
from lib.logging import create_node

# Create main log node
_log = create_node(__name__)

tux=r"""
  .~.
  /V\
 //  \\
/(    )\
 ^`~'^

This floppy drive has passed!
"""

def floppy_scan():
    return (FloppyDevice(),)

class FloppyDevice(test.TestableDevice):

    # English name of the device tested
    name = "Floppy Drive"

    def __init__(self):
        # Create log node for this object
        self.__log = _log.child_node("FloppyDevice")
        # Run inherited __init__
        test.TestableDevice.__init__(self)

    def run_command(self, command):
        self.__log("Run", "Running \"%s\"." % command)
        status, output = commands.getstatusoutput(command)
        self.__log("Run", "Returned Status: %s." % status)
        self.__log("Run", "Returned Output: \"%s\"." % output)
        return status, output

    def _d_test(self):
        userinteraction.prompt("Insert Floppy", "Please put a writable floppy in the drive 'to be tested' and press enter.")

        # badblocks
        userinteraction.notice("Scanning Floppy...")
        status, output = self.run_command("badblocks /dev/fd0 1440")
        if not status==0:
            userinteraction.error("Scan Failed.")
            return test.Status["Failed"]

        # mformat
        userinteraction.notice("Formating Floppy...")
        status, output = self.run_command("mformat a:")
        if not status==0:
            userinteraction.error("Format Failed.")
            return test.Status["Failed"]

        # mount
        userinteraction.notice("Mounting Floppy...")
        status, output = self.run_command("mount -rw /dev/fd0 /floppy/")
        if not status==0:
            userinteraction.error("Mount Failed.")
            return test.Status["Failed"]

        try:
            # copy
            userinteraction.notice("Writing Tux to Floppy...")
            try:
                f = open("/floppy/tux.txt", "w")
                f.write(tux)
                f.close()
            except:
                userinteraction.error("Failed to write Tux.")
                return test.Status["Failed"]
            userinteraction.notice("No errors.")
        finally:
            # unmount
            userinteraction.notice("Unmounting Floppy...")
            status, output = self.run_command("umount /floppy/")
            if not status==0:
                userinteraction.error("Unmount Failed.")
                return test.Status["Failed"]        

        # mount in second drive
        userinteraction.prompt("Switch Drive", "Please put the floppy into the internal floppy drive and press enter.")
        
        userinteraction.notice("Mounting Floppy...")
        status, output = self.run_command("mount /dev/fd1 /floppy/")
        if not status==0:
            userinteraction.error("Mount Failed.")
            return test.Status["Failed"]

        try:
            # read
            userinteraction.notice("Reading Tux from Floppy...")
            try:
                f = open("/floppy/tux.txt", "r")
                data = f.read(-1)
                f.close()
            except:
                userinteraction.error("Failed to read Tux.")
                return test.Status["Failed"]

            if data==tux:
                userinteraction.notice("Data is identical; No errors!")
            else:
                userinteraction.error("Data Differs! Test Failed.")
                return test.Status["Failed"]
            userinteraction.notice("Data: %s" % data)

        finally:
            # unmount
            userinteraction.notice("Unmounting Floppy...")
            status, output = self.run_command("umount /floppy/")
            if not status==0:
                userinteraction.error("Unmount Failed.")
                return test.Status["Failed"]

        # Since nothing failed, pass the test.
        return test.Status["Passed"]

    def _d_data(self):
        return {}

    def _d_description(self, data):
        # Define code to make a description for a Pogo Stick here
        return None

class FloppyTester(test.GizmoTester):

    gizmotype = "Gizmo.Component.Drive.FloppyDrive"

    def run(self):
        # Define test logic for a Pogo Stick here. Usually this is pretty
        # straightforward, like in this case.
        floppies = floppy_scan()
        for floppy in floppies:
            floppy.get_data()
            floppy.test()
        return floppies

def main():
    from lib import testscript
    testscript.start(FloppyTester)

if __name__ == '__main__': main()
