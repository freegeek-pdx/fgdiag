"""Testing API Tester

Runs through some functions of the testing api.

"""

from lib import test

class TestingTest(test.GizmoTest):
        
    def run(self):
        return {"Gizmo.notes":"Everything is working!"}

if __name__ == '__main__': test.start_test(TestingTest)
