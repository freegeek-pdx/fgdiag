"""Python Module for FreeGeek testing."""
import sys

from prompts import prompt_for_gizmos, confirm_data, report_success
from userinteraction import notice, error
from testdata import register_test_data
from config import get_fgdb_login
from errors import InvalidStatusError, DBConnectError
from logging import create_node

_log = create_node(__name__)

class _StatusConstant:

    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __get_data(self):
        return dict(self.data)

    data = property(__get_data, doc="Data for status constant.")

class _StatusConstantCollection(dict):

    def create_status(self, name, data):
        self[name] = _StatusConstant(name, data)

    def remove_status(self, name):
        del self[name]

    def valid_status(self, constant):
        return constant.name in self.keys()

Status = _StatusConstantCollection()

# Statuses:
# Test was inconclusive
Status.create_status("Unknown", {"working":"M", "needsexpert":"M"})
# Gizmo is bad
Status.create_status("Failed", {"working":"N", "needsexpert":"N"})
# Gizmo is good
Status.create_status("Passed", {"working":"Y", "needsexpert":"N"})
# Gizmo is bad, could possibly be fixed by and expert
Status.create_status("NeedsExpert", {"working":"M", "needsexpert":"Y"})

Destination = _StatusConstantCollection()

# Destinations
# We don't know where to put it
Destination.create_status("Unknown", {})
# Recycle it
Destination.create_status("Recycled", {"newStatus":"Recycled"})
# Store it
Destination.create_status("Stored", {"newStatus":"Stored"})

def status_from_boolean(bool):
    if bool:
        return Status["Passed"]
    else:
        return Status["Failed"]

def start_test(test):
    """Helper function. Initializes test and runs its test."""
    testinstance = test()
    testinstance.start_test()
    
class TestableDevice:

    name = "Device"

    def __init__(self):
        self.data = dict()
        self.description = str()
        self.status = Status["Unknown"]
        self.__log = _log.child_node("TestableDevice", self.name)

    def _d_data(self):
        """Provide properties of this device.

        @returns: a mapping of database field names to values.
        @returntype: dict
        """
        raise NotImplementedError

    def _d_description(self, data):
        """Provide a human-readable description of this device.

        @param data: data dictionary as provided by L{_d_data}
        @type data: dict

        @returntype: string
        """
        raise NotImplementedError

    def get_data(self):
        """Fetch data about the Gizmo, and return the results. Sets
        self.data to the data, and self.description to a human
        readable description."""

        self.__log("get_data", "Running _d_data()")
        self.data = self._d_data()
        self.__log("get_data", "Returned %s." % self.data)
        self.__log("description", "Running _d_description()")
        self.description = self._d_description(self.data)
        self.__log("description", "Returned %s." % self.description)
        return self.data

    def _d_test(self):
        """Test the device.

        @returns: status code from test.Status_*
        """
        raise NotImplementedError

    def test(self):
        """Test the Gizmo, and return the status. Sets self.status to
        the status of the Gizmo."""

        self.__log("test", "Running _d_test()")
        self.status = self._d_test()
        self.__log("test", "Returned %s." % self.status)
        return self.status

class GizmoTester:
    """Represents a complete gizmo Test. Inherit and implement run,
    then instantiate and call start_test to use."""
    #def __init__(self, gid=None):
    #    if gid==None:
    #        self.gid = self.prompt()
    #    else:
    #        self.gid = gid

    gizmotype = None

    def __init__(self):
        self.__log = _log.child_node("GizmoTester", self.gizmotype)

    def start_test(self):
        """Test a Gizmo.

        Steps Taken:
        1.  Run the test given as self.run().
        2.  Connect to FGDB.
        3a. Prompt for a Gizmo ID.
        3b. Check and get the Gizmo from the established FGDB connection.
        4.  Put the data into FGDB under the selected Gizmo.

        """

        def connect():
             # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
            from fgdb import connect

            try:
                notice("Connecting to the FreeGeek Database...")
                return connect(*get_fgdb_login())
            except DBConnectError, e:
                # Do any recovery here
                msg = \
                "Unable to connect to the FreeGeek Database.\nError returned: %s" % str(e)
                error(msg)
                raise
            
        self.__log("Start", "Starting test.")

        # Run scan first
        devices = self.scan()
        db = connect()
        devicegizmos = prompt_for_gizmos(db, self.gizmotype, devices)
        db.disconnect()
        
        self.run(devices)

        # Stick instructions in this dict for later
        deviceinstructions = dict()
        
        for device in devices:
            # Set working and needsExpert based on preset constant
            if Status.valid_status(device.status):
                statusdata = device.status.data

                # Update statusdata, so anything in device.data overrides statusdata.
                statusdata.update(device.data)
                
                device.data = statusdata
            else:
                raise InvalidStatusError, device.status

            destination, instructions = self.destination(device)
            if Destination.valid_status(destination):
                destinationdata = destination.data

                # Same
                destinationdata.update(device.data)
                device.data = destinationdata

                deviceinstructions[device] = instructions
            else:
                raise InvalidStatusError, device.status

        db = connect()
        
        if confirm_data(devices, devicegizmos):
            # Kind of dumb to be creating essentially the same list again...
            reportdata = list()
            # start transaction here
            for device in devices:
                gizmo = devicegizmos[device]
                newgizmo = False
                if gizmo is None:
                    # Create Gizmo
                    gizmo = db.get_gizmo_by_id(db.add_gizmo(self.gizmotype))
                    newgizmo = True
                else:
                    gizmo = db.get_gizmo_by_id(gizmo.id)
                reportdata.append((device.name, device.description, gizmo.id, newgizmo, deviceinstructions[device]))
                register_test_data(gizmo, device.data)
            # end transaction here
            db.disconnect()
            notice("Success!")
            report_success(reportdata)
            self.__log("Finish", "Successful finish of test.")
        else:
            #XXX Put some sort of option to restart here
            notice("FIXME: Put an option to restart here")

    def run(self):
        raise NotImplementedError

    def scan(self):
        raise NotImplementedError

    def destination(self, device):
        raise NotImplementedError
