"""Python Module for FreeGeek testing."""
from fgdb import connect, InvalidRowError
from prompts import prompt_for_gizmo
from userinteraction import notice
from testdata import register_test_data
from config import get_fgdb_login

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
        data = self.run()
        
        # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
        db = connect(*get_fgdb_login())
        
        gizmo = prompt_for_gizmo(db, self.gizmotype)
        
        register_test_data(gizmo, data)
        notice("Successfully set %s for gizmo %s" % (", ".join(data.keys()), gizmo.id))

    def run(self):
        raise NotImplementedError