"""Testing API Tester

Runs through some functions of the testing api.

"""

from lib import test

def run(gizmo):
	print "manufacturer:", gizmo.get("manufacturer")
	return {"notes":"Everything is working!"}
	
if __name__ == '__main__': test.start_test(run)
