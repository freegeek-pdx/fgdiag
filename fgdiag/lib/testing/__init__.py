"""Python Module for FreeGeek testing."""

from FGDB import connect
from Prompts import prompt_for_gizmo

FGDBURL = 'mysql://chromakode@localhost/chromakode'

def start_test(runfunc):
	"""Test a Gizmo.
	
	Steps Taken:
	1.  Connect to FGDB.
	2a. Prompt for a Gizmo ID and make sure it is in FGDB.
	2b. Get the Gizmo from the established FGDB connection.
	3.  Run a test in the form of a given function runfunc.
	4.  Put the data returned by the test into FGDB under the selected Gizmo.
	
	Keyword arguments:
	runfunc -- function that implements a test
	
	"""
	
	db = connect(FGDBURL)
	gid = prompt_for_gizmo()
	gizmo = db.get_gizmo_by_id(gid)
	
	data = runfunc(gizmo)
	gizmo.register_test_data(data)
