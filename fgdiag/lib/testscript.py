"""Testing API Tester

Runs through some functions of the testing api.

"""

import testing

def run(gizmo):
	print gizmo.manufacturer
	return {'working':True}
	
if __name__ == '__main__': testing.start_test(run)
