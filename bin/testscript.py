"""Testing API Tester

Runs through some functions of the testing api.

"""

from fgdiag.lib import test

def __run__(gizmo):
    print gizmo.manufacturer
    return {'working':True}

if __name__ == '__main__':
    test.start_test(__run__)
