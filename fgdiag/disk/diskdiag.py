"""Disk diagnostics
"""

from fgdiag.lib import test
from fgdiag.lib import userinteraction as ui
from subprocess import call, Popen
import cursesdisk
import disk

SMARTCTL = "/usr/sbin/smartctl"
DD = "/bin/dd"
CLONER = "/usr/bin/cloner"

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

    def smart_test(self):
        retcode = call([SMARTCTL, "-q", "silent", "--all", self.dev])
        if retcode > 4:
            self.status = test.Status["Failed"]
            print "Drive failed smartctl test with a return of '%d'" % (retcode)

    def dd_wipe(self, wipe_type="urandom"):
        try:
            proc = Popen([DD, "of=%s" % self.dev, "if=/dev/%s" % wipe_type, "bs=1024"])
        except OSError, e:
            pass
        return proc

    def install_os(self):
        try:
            proc = Popen([CLONER, "default"], stdout="/dev/null", env={"INTERACTVE": "false"})
        except OSError, e:
            pass
        return proc

    def further_tests_needed(self):
        return self.status != test.Status["Failed"]

class DiskDiag(test.GizmoTester):
    def scan(self):
        ui.notice("Scanning for devices to check")
        devs = disk.findSysDevicesToScan()
        if not devs:
            ui.error_exit("Found no disks to scan!")
        return devs

    def run(self, devs):
        ui.prompt("About to commence tests.", "Press enter to begin. ")
        disk.smart_test(devs)
        failed = False
        for dev in devs:
            if not dev.further_tests_needed():
                failed = True
        if failed:
            ui.prompt("Some drives have already failed; it may be more efficient to remove said drive(s) now and restart the tests.")
        cursesdisk.run('badblocks', devs)
        disk.smart_test(devs)
        disk.dd_wipe(devs)
        disk.smart_test(devs)
        #disk.install_os(devs)
        disk.smart_test(devs)
        ui.notice("Done testing. Status report")
        for i in devs:
            print "%s: %s" % (i, i.status)

    def destination(self, dev):
        if dev.status == test.Status["Passed"]:
            return test.Destination["Stored"], "Good HD: label it and put it away."
        else:
            return test.Destination["Recycled"], "Dead HD: smash it, recycle it."
