"""Disk diagnostics
"""

from fgdiag.lib import test
from fgdiag.lib import userinteraction as ui
import cursesdisk
import disk

class DiskDevice(test.TestableDevice):
    name = "Hard Disk"

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

    def _d_scsidata(self):
        self.data["sizeMb"] = disk.getDeviceSize(self.dev) / (1024**2)
        id = disk.ScsiIdentification(self.dev)
        self.data["modelNumber"] = id["model"]
        return self.data

    def _d_description(self, data):
        return self.dev + ": " + str(self.data["sizeMb"]) + "MB"

    def __str__(self):
        return self.dev

class DiskDiag(test.GizmoTester):
    def scan(self):
        ui.notice("Scanning for devices to check")
        devs = disk.findSysDevicesToScan()
        if not devs:
            ui.error_exit("Found no disks to scan!")
        return devs

    def run(self, devs):
        ui.prompt("About to commence scan.", "Press enter to begin. ")
        disk.smart_test(devs)
        cursesdisk.run(devs)
        disk.smart_test(devs)
        disk.dd_wipe(devs)
        disk.smart_test(devs)
        disk.install_os(devs)
        disk.smart_test(devs)
        ui.notice("Done testing. Status report")
        for i in devs:
            print "%s: %s" % (i, i.status)

    def destination(self, dev):
        if dev.status == test.Status["Passed"]:
            return test.Destination["Stored"], "Good HD. Put it in the good bin."
        else:
            return test.Destination["Recycled"], "Dead. Recycle it."
