#!/usr/bin/env python
# $Id$
# November 2001, Kevin Turner <acapnotic@foobox.org>
# Written for Free Geek

"""Attempts to determine the speed of modems on the serial ports.
"""

# Depends: setserial, Python (version >= 1.5.2)

SETSERIAL="/bin/setserial"
import errno, os, re, string, sys, time, types
try:
    import warnings
except ImportError:
    pass
else:
    # TERMIOS is depreciated (use termios instead)
    # but we still have python1.5 on the modem tester, so don't switch
    # over yet -- just ignore the warning.
    warnings.filterwarnings("ignore", module="TERMIOS")
import fcntl, FCNTL, termios, TERMIOS

# sibling import
from fgdiag.lib import pyutil
from fgdiag.lib.pyutil import bold

_DEBUG = False

def get_serial_devices():
    """Checks devices /dev/ttyS0 - ttyS3 for a UART, which indicates a live device.
    """
    setserial = os.popen("%s -g /dev/ttyS[0123]" % (SETSERIAL,), 'r')
    output = setserial.readlines()
    setserial_error = setserial.close()
    if setserial_error:
        raise RuntimeError("%s returned with exit code %s" %
                           (SETSERIAL, setserial_error))
    r = re.compile("^/dev/ttyS(?P<dev>\d), UART: (?P<uart>.*?),")

    results = []

    for l in output:
        mo = r.search(l)
        if mo is None:
            raise RuntimeError, "Eek, %s didn't match!" % (l,)
        elif mo.group('uart') != "unknown":
            results.append(mo.group('dev'))

    return results

# TODO: Provide the option of using regex's, so we can
# get around the "256K looks like 56K" issue.
speeds = [
    ('003', ("V.21",)),
    ('012', ("V.22","V.23")),
    ('024', ("V.22bis",)),
    ('096', ("V.32",)),
    ('144', ("V.32bis", "V.34","14400","14.4","14,400")),
    ('288', ("V.34", "28800","28.8")),
    ('336', ("V.34bis", "V.34+", "33600", "33.6")),
    ('560', ("V.90", "56000", "56.", re.compile("[^2]56k"))),
    ]

# Test fastest -> slowest
speeds.reverse()

STOP_STRINGS = ("ERROR",)
IGNORE_STRINGS = ("OK",)

TIMEOUT_SECS = 5.0

# Some USR modems are very considerate.
ANY_KEY = "Strike a key when ready"

def find_speed(modem, outputFunc=None):
    """Treat a file-like object as a modem, and try to determine its speed.

    @param outputFunc: Where to send the modem's responses.  Defaults to
        L{sys.stdout}.write.
    @type outputFunc: callable
    """

    if outputFunc is None:
        outputFunc = sys.stdout.write

    # TODO: Sportsters rock, but we should special-case them to avoid
    # getting lots more diagnostics than we want.

    canidates = []
    for i in xrange(16):
        writestring = "ATI%d" % (i,)
        modem.write(writestring + '\n')
        response = ''
        gotEcho = False

        pulse = time.time()

        first_line = True
        while first_line or response:
            # XXX: Kludge!  But it takes the modem a bit to respond.
            time.sleep(0.05)
            response = modem.readline()
            stripped = string.upper(string.strip(response))

            if response == '':
                # No data to read.
                if (time.time() - pulse ) > TIMEOUT_SECS:
                    if gotEcho:
                        # I've got a modem here that doesn't even say
                        # "OK" if you ask it about ATI9, but it's already
                        # given us the data by now.
                        if _DEBUG:
                            print "Timed out but got AT echo, moving on."
                        break
                    else:
                        raise IOError(errno.ETIME,
                                      "Giving up after %0.1f seconds without response."
                                      % (time.time() - pulse,),
                                      modem.name)
                else:
                    pass
            elif stripped == '':
                # Got a blank line.
                pulse = time.time()
            elif stripped in STOP_STRINGS:
                if _DEBUG:
                    print "Stopping at level %d" % (i,)
                return canidates
            elif stripped == writestring:
                # This is our command echo'd back to us?
                pulse = time.time()
                gotEcho = True
                if _DEBUG:
                    print "I%d: %s" % (i, stripped)
            elif stripped[:len(ANY_KEY)] == ANY_KEY:
                modem.write("\n")
            else:
                pulse = time.time()

                first_line = False
                if (stripped not in IGNORE_STRINGS) or _DEBUG:
                    outputFunc("I%d: %s\n" % (i, stripped))
                if stripped == "OK":
                    continue

                # Eat spaces for comparison
                nospace = string.replace(stripped, ' ','')
                for speed, strings in speeds:
                    # Are any of the strings for this speed found here?
                    found = filterfunc(nospace, strings)
                    ## found = filter(lambda s,r=string.upper(nospace):
                    ##               string.find(r, string.upper(s)) != -1,
                    ##               strings)
                    if found:
                        if _DEBUG:
                            print found
                        canidates.append((speed, stripped))
                        break

    return canidates

def filterfunc(subject, patterns):
    for pattern in patterns:
        if type(pattern) is types.StringType:
            if string.find(string.upper(subject), string.upper(pattern)) != -1:
                return True
        elif pattern.search(subject) is not None:
            return True
    return False

def open_modem(dev):
    """Open a modem device and set it to non-blocking.

    Returns a file object.
    """
    dev = "/dev/ttyS%s" % (dev,)
    f = open(dev, "r+", 0)
    fd = f.fileno()

    mode = termios.tcgetattr(fd)
    mode[3] = mode[3] & ~TERMIOS.ECHO

    cc = mode[-1]
    cc[TERMIOS.VMIN] = 0
    cc[TERMIOS.VTIME] = 0
    # VMIN - minimum characters to receive
    # VTIME - maximum time to wait
    # (unset both for non-blocking)
    termios.tcsetattr(fd, TERMIOS.TCSANOW, mode)
    fcntl.fcntl(fd,FCNTL.F_SETFL,FCNTL.O_NONBLOCK)

    return f

def flush_modem(modem):
    modem.write("\r\n")
    modem.write("\r\n")
    modem.write("ATZ\n")
    time.sleep(1.5)
    while 1:
        time.sleep(0.05)
        l = modem.readline()
        if not l:
            break
    # TODO: Test for "OK"?
    return

def is_modem(modem):
    isModem = False
    flush_modem(modem)
    modem.write("AT\n")
    while 1:
        time.sleep(0.05)
        l = modem.readline()
        if not l:
            break
        elif l[:2] == "OK":
            isModem = True
    return isModem

def make_modem_link():
    live_ports = get_serial_devices()
    if not live_ports:
        print bold("No active serial ports found.")
        return

    for dev in live_ports:
        modem = open_modem(dev)

        try:
            if is_modem(modem):
                if os.path.exists("/dev/modem"):
                    os.unlink("/dev/modem")
                os.symlink("/dev/ttyS%s" % (dev,), "/dev/modem")
                print "Linked /dev/ttyS%s to /dev/modem" % (dev,)
                linked = dev
        finally:
            modem.close()

        if linked:
            return linked
    else:
        print "Couldn't determine modem device, link not made."
        return None

def main():
    """Test modem speeds on all live ports and print the results.
    """
    try:
        import pcimodem
    except ImportError:
        pass
    else:
        pcimodem.main()

    try:
        import isapnp
    except ImportError:
        pass
    else:
        isapnp.main()

    live_ports = get_serial_devices()
    if not live_ports:
        print bold("No active serial ports found.")
    else:
        print "Live serial devices:", string.join(live_ports, ", ")

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
            else:
                print "I found conflicting evidence for /dev/ttyS%s:" % (bold(str(dev)),)
                for r in results:
                    print "(%s?) %s" % r


if __name__ == '__main__':
    pyutil.withPager(main)
