"""Python Module for FreeGeek testing."""
import sys

from fgdb import connect, InvalidRowError
from prompts import prompt_for_gizmo, confirm_data
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

Status_Failed = 0
Status_Passed = 1
Status_Expert = 2

def start_test(test):
    """Helper function. Initializes test and runs it's test."""
    testinstance = test()
    testinstance.start_test()

class GizmoTest:
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
        status, data = self.run()
        
        # Set working and needsExpert based on preset constant
        if status == Status_Failed:
            data["working"] = "N"
            data["needsExpert"] = "N"
        elif status == Status_Passed:
            data["working"] = "Y"
            data["needsExpert"] = "N"
        elif status == Status_Expert:
            data["working"] = "M"
            data["needsExpert"] = "Y"
        else:
            raise InvalidStatusError, status 
            
        # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
        db = connect(*get_fgdb_login())

        gizmo = prompt_for_gizmo(db, self.gizmotype)

        if confirm_data(data, gizmo.id):
            register_test_data(gizmo, data)
            notice("Success!")
        else:
            #XXX Put some sort of option to restart here
            notice("FIXME: Put an option to restart here")

    def run(self):
        raise NotImplementedError
