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
Status.create_status("Unknown", {"working":"M", "needsexpert":"M"})
Status.create_status("Failed", {"working":"N", "needsexpert":"N"})
Status.create_status("Passed", {"working":"Y", "needsexpert":"N"})
Status.create_status("NeedsExpert", {"working":"M", "needsexpert":"Y"})

Destination = _StatusConstantCollection()
Destination.create_status("Unknown", {})
Destination.create_status("Recycled", {"newstatus":"Recycled"})
Destination.create_status("Stored", {"newstatus":"Stored"})

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

        self.__log("Start", "Starting test.")

        # Run test first
        devices = self.run()

        for device in devices:
            # Set working and needsExpert based on preset constant
            if Status.valid_status(device.status):
                statusdata = device.status.data

                # Update statusdata, so anything in device.data overrides statusdata.
                device.data = statusdata.update(device.data)
            else:
                raise InvalidStatusError, device.status

        # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
        from fgdb import connect

        try:
            notice("Connecting to the FreeGeek Database...")
            db = connect(*get_fgdb_login())
        except DBConnectError, e:
            # Do any recovery here
            msg = \
            "Unable to connect to the FreeGeek Database.\nError returned: %s" % str(e)
            error(msg)
            raise
        
        devicegizmos = prompt_for_gizmos(db, self.gizmotype, devices)

        # Replace with something more efficient
        data = list()
        for device, gizmo in devicegizmos.iteritems():
            if gizmo is not None:
                id_ = gizmo.id
            else:
                id_ = None
            data.append((device.name, device.description, id_))

        if confirm_data(data):
            # Kind of dumb to be creating essentially the same list again...
            reportdata = list()
            # start transaction here
            for device, gizmo in devicegizmos.iteritems():
                newgizmo = False
                if gizmo is None:
                    # Create Gizmo
                    gizmo = db.get_gizmo_by_id(db.add_gizmo(self.gizmotype))
                    newgizmo = True
                reportdata.append((device.name, device.description, gizmo.id, newgizmo))
                register_test_data(gizmo, device.data)
            # end transaction here
            notice("Success!")
            report_success(reportdata)
            self.__log("Finish", "Successful finish of test.")
        else:
            #XXX Put some sort of option to restart here
            notice("FIXME: Put an option to restart here")

    def run(self):
        raise NotImplementedError
