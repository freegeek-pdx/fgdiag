"""Python Module for FreeGeek testing."""
import sys

from prompts import prompt_for_ids, confirm_data
from userinteraction import notice, error
from testdata import register_test_data
from config import get_fgdb_login
from errors import InvalidStatusError, DBConnectError
from logging import create_node

_log = create_node(__name__)


# TODO: Collect these into a container of some kind.
# Would it make more sense for Status_Unknown to be 0, and Status_Failed to be -1?
Status_Unknown = -1
Status_Failed = 0
Status_Passed = 1
Status_Expert = 2

def status_from_boolean(bool):
    if bool:
        return Status_Passed
    else:
        return Status_Failed

def start_test(test):
    """Helper function. Initializes test and runs its test."""
    testinstance = test()
    testinstance.start_test()

class TestableDevice:

    name = "Device"

    def __init__(self):
        self.data = dict()
        self.description = str()
        self.status = Status_Unknown
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
        self.__log("get_data", "Returned %s." % self.status)
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
            if device.status == Status_Failed:
                device.data["working"] = "N"
                device.data["needsExpert"] = "N"
            elif device.status == Status_Passed:
                device.data["working"] = "Y"
                device.data["needsExpert"] = "N"
            elif device.status == Status_Expert:
                device.data["working"] = "M"
                device.data["needsExpert"] = "Y"
            elif device.status == Status_Unknown:
                # Do something special?
                device.data["working"] = "M"
                device.data["needsExpert"] = "M"
            else:
                raise InvalidStatusError, status

        # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
        from fgdb import connect

        try:
            notice("Connecting to the Free Geek Database...")
            db = connect(*get_fgdb_login())
        except DBConnectError, e:
            # Do any recovery here
            msg = \
            "Unable to connect to the Free Geek Database.\nError returned: %s" % str(e)
            error(msg)
            raise
        
        devicegizmos = prompt_for_ids(db, self.gizmotype, devices)

        # Replace with something more efficient
        iddata = dict()
        for device, gizmo in devicegizmos.iteritems():
            iddata[gizmo.id] = device.data

        if confirm_data(iddata):
            for device, gizmo in devicegizmos.iteritems():
                register_test_data(gizmo, device.data)
            notice("Success!")
            self.__log("Finish", "Successful finish of test.")
        else:
            #XXX Put some sort of option to restart here
            notice("FIXME: Put an option to restart here")

    def run(self):
        raise NotImplementedError
