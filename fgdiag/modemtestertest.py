from modem.modem import *
from lib import test

class TestingTest(test.GizmoTest):

    gizmotype = "Gizmo.Component.Printer"
    
    def run(self):
        for dev in live_ports:
            print "Testing device %s" % (dev,)
            try:
                modem = open_modem(dev)
            except termios.error, e:
                if e[0] == errno.EIO:
                    print ("ttyS%s won't speak to me."
                           "  (%s opening device)" % (e[1], dev,))
                else:
                    raise
            results = None
            try:
                flush_modem(modem)
                try:
                    results = find_speed(modem)
                except IOError, e:
                    # Catch timeouts.
                    if e.errno == errno.ETIME:
                        print "%s: %s" % (e.filename, e.strerror)
                    else:
                        raise
            finally:
                modem.close()

            print ''
            if not results:
                print "I couldn't determine the modem speed.  Can you?"
            else:
                same = False
                r = results[:]
                sameas = r.pop(0)[0]
                while r:
                    if sameas == r.pop(0)[0]:
                        same = True
                    else:
                        same = False
                        break
                if same or (len(results) == 1):
                    print "I'm pretty sure that"
                    print "device ttyS%s is speed %s" % (bold(str(dev)),
                                                         bold(results[0][0]))
                    return {"speed",results[0][0]}
                else:
                    print "I found conflicting evidence for /dev/ttyS%s:" % (bold(str(dev)),)
                    for r in results:
                            print "(%s?) %s" % r
                    return None

def main()
    test.start_test(TestingTest)

if __name__ == '__main__': main()

