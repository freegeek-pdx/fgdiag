"""Testing API Tester

Runs through some functions of the testing api.

"""

from lib import test
import time

class TestingTest(test.GizmoTest):

    gizmotype = "Gizmo.Component.Printer"
    
    def run(self):
        #time.sleep(5)
        return {"Gizmo.notes":"Everything is working!"}

if __name__ == '__main__': test.start_test(TestingTest)