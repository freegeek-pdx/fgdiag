"""Python Module for FreeGeek testing."""

def start_test(runfunc):
    """Test a Gizmo.
    
    Steps Taken:
    1.  Connect to FGDB.
    2.  Prompt for a Gizmo ID.
    3.  Get the Gizmo from the established FGDB connection.
    4.  Run a test in the form of a given function runfunc.
    5.  Process returned test data
    6.  Put the data into FGDB under the selected Gizmo.
    
    Keyword arguments:
    runfunc -- function that implements a test
    
    """
    
    from fgdb import connect
    from prompts import prompt_for_gizmo
    from userinteraction import notice
    from testdata import register_test_data
    from config import get_fgdb_login
    
    # Is it safe to store the password for the user (write+read permissions in fgdb) in plaintext?
    FGDBHOST, FGDBDB, FGDBUSER, FGDBPASSWD = get_fgdb_login()
    
    db = connect(FGDBHOST, FGDBDB, FGDBUSER, FGDBPASSWD)
    gid = prompt_for_gizmo()
    gizmo = db.get_gizmo_by_id(gid)
    
    data = runfunc(gizmo)
    
    register_test_data(gizmo, data)
    notice("Successfully set %s for gizmo %s" % (" ,".join(data.keys()), gizmo.id))
    
