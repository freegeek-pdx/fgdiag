# -*- Python -*-
# $Id$

# updated for scsi by Kyle L. // kysle@hotmail.com


"""Disk diagnostics
"""

from fgdiag.lib import test
from fgdiag.lib import userinteraction as ui
import cursesdisk
import disk

class DiskDevice(test.TestableDevice):
    name = "SCSI Hard Drive"

    def __init__(self, dev):
        test.TestableDevice.__init__(self)
        self.dev = dev

    def _d_test(self):
        pass

    def _d_data(self):
        self.data["sizeMb"] = disk.getDeviceSize(self.dev) / (1024**2)
        id = disk.identification(self.dev)
        self.data["modelNumber"] = id["model"]
        return self.data

    def _d_description(self, data):
        return self.dev + ": " + str(self.data["sizeMb"]) + "MB"

    def __str__(self):
        return self.dev

class DiskDiag(test.GizmoTester):
    gizmotype = "Gizmo.Component.Drive.SCSIHardDrive"

    def scan(self):
        ui.notice("Scanning for devices to check")
        try:
            devs = disk.findBlockDevicesToScan()
        except disk.QuestionablePartitionException, qpe:
            drivestr = ""
            for i in qpe.args[0]:
                drivestr += "\n%s: %#04x" % (i[0], i[1])
            prompt = """There are some weird partitions on one or more of the drives:%s
Do you want to continue and clobber these partitions (no to abort and put
it on the "weird" pile)?""" % (drivestr,)
            if ui.yesno("Questionable Partitions", prompt):
                devs = disk.findBlockDevicesToScan(forceClobber=True)
            else:
                ui.error_exit("Stopping.")
        if not devs:
            ui.error_exit("Found no disks to scan!")
        return devs

    def run(self, devs):
        ui.prompt("About to commence scan.", "Press enter to begin. ")
        cursesdisk.run(devs)
        ui.notice("Done. Status report")
        for i in devs:
            print "%s: %s" % (i, i.status)

    def destination(self, dev):
        if dev.status == test.Status["Passed"]:
            return test.Destination["Stored"], "Good HD. Put it in the good bin."
        else:
            return test.Destination["Recycled"], "Dead. Recycle it."

if __name__ == "__main__":
    DiskDiag().start_test()
