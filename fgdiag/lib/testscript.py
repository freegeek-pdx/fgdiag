import sys, getopt
from test import start_test
from logging import PrintReceptor, add_receptor

usage = """Free Geek Gizmo Tester
Tests "%s"

Options:
  -h  This help text.
  -d  Show debugging output."""

def start(test):
    """Call from a FreeGeek test script with a testabledevice class. Handles command line arguments."""
    opts, args = getopt.getopt(sys.argv[1:], 'dh', ['debug', 'help'])

    for o, a in opts:
        if o in ('-d', '--debug'):
            add_receptor("debug", PrintReceptor())
        if o in ('-h', '--help'):
            print usage % test.gizmotype
            sys.exit(0)
    start_test(test)
