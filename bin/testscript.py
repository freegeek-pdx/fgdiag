"""Testing API Tester

Runs through some functions of the testing api.

"""

from fgdiag.lib import testing

def __run__(gizmo):
    print gizmo.manufacturer
    return {'working':True}

if __name__ == '__main__': testing.start_test(__run__)
