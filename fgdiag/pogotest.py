"""Testing API Tester

Runs through some functions of the testing api.

"""

from lib import test, userinteraction

def pogo_scan():
    # Define code to find avaliable Pogo Sticks here. Since there is no feasible
    # way to detect this from the computer, just create a PogoDevice instance
    # and stick it in a sequence.
    return (PogoDevice(),)

class PogoDevice(test.TestableDevice):

    # English name of the device tested
    name = "Pogo Stick"

    def _d_test(self):
        # Define code to Test a Pogo Stick here
        working = userinteraction.yesno("Does the pogo stick work?", "Please bring the pogo stick to a hard and flat surface and try it out. Does it work?")
        return test.status_from_boolean(working)

    def _d_data(self):
        # Define code to get data on a Pogo Stick here
        color = userinteraction.prompt("Color?", "What color is the pogo stick?")
        return {"notes":"Colored %s"%color}

    def _d_description(self, data):
        # Define code to make a description for a Pogo Stick here
        return data["notes"]

class PogoTester(test.GizmoTester):

    #gizmotype = "Gizmo.Other"
    gizmotype = "Gizmo.Component.Printer"

    def run(self):
        # Define test logic for a Pogo Stick here. Usually this is pretty
        # straightforward, like in this case.
        pogos = pogo_scan()
        for pogo in pogos:
            pogo.get_data()
            status = pogo.test()
        return pogos

def main():
    test.start_test(PogoTester)

if __name__ == '__main__': main()
