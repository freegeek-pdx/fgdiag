"""Python Module for FreeGeek testing."""
import sys

from fgdb import connect, InvalidRowError
from prompts import prompt_for_ids, confirm_data
from userinteraction import notice
from testdata import register_test_data
from config import get_fgdb_login

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InvalidStatusError(Error):
    """Exception raised when an invalid status is returnedby a test."""
    def __init__(self, status):
        self.status = status
    def __str__(self):
        return repr(self.status)

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
    """Helper function. Initializes test and runs it's test."""
    testinstance = test()
    testinstance.start_test()

class TestableDevice:

    name = "Device"
    
    def __init__(self):
        self.data = dict()
        self.description = str()
        self.status = Status_Unknown
        
    def _d_data(self):
        raise NotImplementedError
        
    def _d_description(self, data):
        raise NotImplementedError
        
    def get_data(self):
        """Fetch data about the Gizmo, and return the results. Sets self.data to the data, and self.description to a human readable description."""
        self.data = self._d_data()
        self.description = self._d_description(self.data)
        return self.data

    def _d_test(self):
        raise NotImplementedError

    def test(self):
        """Test the Gizmo, and return the status. Sets self.status to the status of the Gizmo."""
        self.status = self._d_test()
        return self.status

class GizmoTester:
    """Represents a complete gizmo Test. Inherit and implement run, then instantiate and call start_test to use."""
    #def __init__(self, gid=None):
    #    if gid==None:
    #        self.gid = self.prompt()
    #    else:
    #        self.gid = gid
    
    gizmotype = None
    
    def start_test(self):
        """Test a Gizmo.
        
        Steps Taken:
        1.  Run the test given as self.run().
        2.  Connect to FGDB.
        3a. Prompt for a Gizmo ID.
        3b. Check and get the Gizmo from the established FGDB connection.
        4.  Put the data into FGDB under the selected Gizmo.
        
        """
        
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
        db = connect(*get_fgdb_login())
    
        devicegizmos = prompt_for_ids(db, self.gizmotype, devices)
        
        # Replace with something more efficient
        iddata = dict()
        for device, gizmo in devicegizmos.iteritems():
            iddata[gizmo.id] = device.data
    
        if confirm_data(iddata):
            for device, gizmo in devicegizmos.iteritems():
                register_test_data(gizmo, device.data)
                notice("Success!")
        else:
            #XXX Put some sort of option to restart here
            notice("FIXME: Put an option to restart here")

    def run(self):
        raise NotImplementedError
