"""Testing API Tester

Runs through some functions of the testing api.

"""

from lib import test, userinteraction

class TestingTest(test.GizmoTest):

    #gizmotype = "Gizmo.Other"
    gizmotype = "Gizmo.Component.Printer"
    
    def run(self):
        working = userinteraction.yesno("Does the pogo stick work?", "Please bring the pogo stick to a hard and flat surface and try it out. Does it work?")
        
        status = None
        data = {}
        if working:
            status = test.Status_Passed
        else:
            status = test.Status_Failed
            
        return status, data

def main():
    test.start_test(TestingTest)

if __name__ == '__main__': main()
