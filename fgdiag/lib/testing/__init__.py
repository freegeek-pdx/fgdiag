"""Python Module for FreeGeek testing."""

FGDBURL = 'mysql://chromakode@localhost/chromakode'

def start_test(runfunc):
	"""Test a Gizmo.
	
	Steps Taken:
	1.  Connect to FGDB.
	2.  Prompt for a Gizmo ID.
	3.  Get the Gizmo from the established FGDB connection.
	4.  Run a test in the form of a given function runfunc.
	5.  Process returned test data and translate parameters into Table locations.
	6.  Put the data into FGDB under the selected Gizmo.
	
	Keyword arguments:
	runfunc -- function that implements a test
	
	"""
	
	from FGDB import connect
	from Prompts import prompt_for_gizmo
	from TestData import process
	
	db = connect(FGDBURL)
	gid = prompt_for_gizmo()
	gizmo = db.get_gizmo_by_id(gid)
	
	data = runfunc(gizmo)
	data = process(data, db.field_map)
	
	gizmo.register_test_data(data)
