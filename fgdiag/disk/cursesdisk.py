#!/usr/bin/env python
# $Id$

"""Curses front-end to disk testing module.

@var MINIMUM_SIZE: Do not recommend testing disks with fewer than this many
    bytes.
"""

import curses, math, os, string, sys, time
try:
    from mx import DateTime
except ImportError:
    import DateTime

# sibling import
import disk, badblocks # , klogd
from fgdiag.lib import pyutil, test

try:
    import meminfo
except ImportError:
    meminfo = None

badblocks.mainloop_hooks.append(curses.doupdate)

True = (1==1)
False = not True

MEMINFO_SPAM = None
VERBOSE = False

KLOG_PIPE = "/var/log/kmsg.pipe"

kB = 2L ** 10
MB = 2L ** (10+10)
GB = 2L ** (10+10+10)

MINIMUM_SIZE = 250 * MB

_FIRST_PAIR_NUMBER = 1
pairdefs = [
    (None, curses.A_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK),
    ('okay', curses.A_NORMAL, curses.COLOR_GREEN, curses.COLOR_BLACK),
    ('error', curses.A_BOLD, curses.COLOR_RED, curses.COLOR_BLACK),
    ('success', curses.A_BOLD, curses.COLOR_GREEN, curses.COLOR_BLACK),
    ('progress-none', curses.A_DIM, curses.COLOR_WHITE, curses.COLOR_BLACK),
    ('progress-once', curses.A_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK),
    ('progress-twice', curses.A_BOLD, curses.COLOR_WHITE, curses.COLOR_BLACK),
    ('primary-border', curses.A_NORMAL, curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    ('secondary-border', curses.A_BOLD, curses.COLOR_BLUE, curses.COLOR_BLACK),
    ('primary-label', curses.A_BOLD, curses.COLOR_WHITE, curses.COLOR_MAGENTA),
    ('secondary-label', curses.A_BOLD, curses.COLOR_WHITE, curses.COLOR_BLUE),
    ]


_color_pair = {}

class BadblocksWidget(badblocks.BadblocksObserver):
    """I am the visual representation of the running Badblocks.

    @ivar dev: The device I am showing.
    @type dev: L{diskdiag.DiskDevice}
    """
    PHASE_ROW = 5
    TOP = 1
    BOTTOM = 3
    PROGRESS1_ROW = BOTTOM
    PROGRESS2_ROW = TOP
    SUMMARY_ROW = 0
    pattern = ""
    dev = None

    def __init__(self, bbObject, row=0, column=0, width=20, height=14):
        """Construct a widget from a badblocks object.

        bbObject is a badblocks.Badblocks object.
        row, column are starting coordinates.
        """
        border = curses.newwin(height, width, row, column)
        border.box()
        border.nooutrefresh()
        w = border.derwin(height-2, width-2, 1, 1)
        self.width = width
        self.window = w
        self.border = border

        self.progress1 = ProgressBar(border, self.PROGRESS1_ROW+1, 1, width-2)
        self.progress2 = ProgressBar(border, self.PROGRESS2_ROW+1, 1, width-2)

        self.msgwin = border.derwin(height - 8, width-2, 7, 1)
        self.msgwin.scrollok(1)

        self.window.addstr(self.SUMMARY_ROW, 0,
                           "No problems found yet...",
                           _color_pair["okay"])
        self._observed = bbObject.addObserver(self)
        self.setBlockDevice(bbObject)

        w.nooutrefresh()

    def setBlockDevice(self, bb, description=None):
        """Called to set the label identifying the device being processed.

        @param bb: the Badblocks I am to display the progress of.
        @type bb: L{badblocks.Badblocks}

        @returns: None
        """
        self.dev = bb.device
        # XXX: sloppy
        if string.find(self.dev.dev, 'hdb') != -1:
            channel = "secondary"
        else:
            channel = "primary"
        self.border.attrset(_color_pair["%s-border" % (channel,)])
        self.border.box()
        self.border.addstr(0, 1, self.dev.dev,
                           _color_pair["%s-label" % (channel,)])
        self.border.attrset(_color_pair[None])
        self.border.nooutrefresh()

    def set_operation(self, op):
        """Called to set the label identifying the current scanning operation.
        """
        self._reallySet("operation", op)
        self.window.addstr(self.PHASE_ROW, 0,
                           "%s %s" % (self.operation, self.pattern))

    def set_pattern(self, pattern):
        """Called to set the label identifying the scan pattern in use.
        """
        self._reallySet("pattern", pattern)
        if pattern:
            self.window.addstr(self.PHASE_ROW, 0,
                               "%s %s" % (self.operation, self.pattern))
        else:
            self.window.move(self.PHASE_ROW, 0)
            self.window.clrtoeol()

    def set_runningCount(self, count):
        self._reallySet("runningCount", count)

    def set_totalSumCount(self, count):
        self._reallySet("totalSumCount", count)

    def progress(self, numerator, denominator):
        """Set the progress meter.

        numerator and denominator are numeric types.
        """
        plus = ((self.pattern and (self.operation == "Reading")) and 1.0) or 0.0
        percentage = numerator/float(denominator)
        self.progress1.set_progress(percentage + plus)

        ds = "%.1fk/%.1fk" % (numerator /1024.0, denominator/1024.0)
        ps = "%2.1f%%" % (100 * percentage,)
        spacer = " " * max(0, (self.width - 2 - len(ds) - len(ps)))
        self.window.addstr(self.PROGRESS1_ROW + 1, 0, "%s%s%s" % (ds, spacer, ps))

        if self.totalSumCount:
            # in the case that we're all done, make sure progress meter
            # displays 100 rather than (x+b)/x
            if self.totalSumCount == self.runningCount:
                percentage = 1.0
            else:
                percentage = (numerator + self.runningCount)/float(self.totalSumCount)

            self.progress2.set_progress(percentage)

            ps = "Total%%%ds" % (self.width - 5 - 2,)
            ps = ps % ("%2.1f%%" % (100 * percentage,),)
            self.window.addstr(self.PROGRESS2_ROW + 1, 0, ps)

        self.window.refresh()

    def foundBadblock(self, sector):
        """Called when a bad block has been found.

        sector identifies the sector of the bad block.
        """
        if self._observed:
            self._writeErrorStatus()

        self.msgwin.addstr("%s\n" % (sector,))
        self.msgwin.refresh()

    def klog(self, msg):
        """Display a kernel message in this widget.
        """
        self._writeErrorStatus()
        self.msgwin.addstr("%s\n" % (msg,))
        self.msgwin.refresh()

    def _writeErrorStatus(self):
        """Update the error-status summary line.
        """
        self.window.move(self.SUMMARY_ROW, 1)
        self.window.clrtoeol()
        self.window.addstr(self.SUMMARY_ROW, 0,
                           "%s bad sectors & %d kernel errors" %
                           (len(self._observed.badlist),
                            self._observed.kmsg_count),
                           _color_pair["error"])
        self.window.refresh()

    def finished(self, exitCode=None):
        """Called when the badblocks process is done.
        """
        status = test.Status["Passed"]

        # if the badblocks process exited with an exitCode of 0, then it died naturally
        if not exitCode:
            self.msgwin.addstr("%s of %s complete:\n" % (self._observed.modeLabel,
                                                         self.dev.dev))
            seconds_elapsed = time.time() - self._observed.startTimes[0]
            megabytes = self.dev.data["sizeMb"]
            self.msgwin.addstr("%s elapsed, %s per hundred megabytes.\n" % (
                str(DateTime.TimeDelta(seconds = seconds_elapsed)),
                str(DateTime.TimeDelta(seconds = seconds_elapsed /
                                       (megabytes / 100.0)))))
        else:
            self.msgwin.addstr("The badblocks process was killed.\n")
            status = test.Status["NeedsExpert"]

        if self._observed.badlist:
            self.msgwin.addstr("%d bad sectors found. :(\n" % (len(self._observed.badlist),))
            status = test.Status["Failed"]

        if status == test.Status["Passed"]:
            self.msgwin.addstr("PASSED", _color_pair['success'])
            self.progress(self._observed.sectorCount, self._observed.sectorCount)

        self.dev.status = status

        self.msgwin.refresh()


class ProgressBar:
    """I display a progress bar on screen.
    """

    def __init__(self, parent, row=0, column=0, width=10):
        """Construct a progress bar in an ncurses window.

        @param parent: the ncurses window I live in.
        @param row: row of the window to display in
        @type row: int
        @param column: first column
        @type column: int
        @param width: width of the progress bar, in characters
        @type width: int
        """
        self.chars = {'none': (curses.ACS_BOARD, _color_pair['progress-none']),
                      'once': (curses.ACS_CKBOARD, _color_pair['progress-once']),
                      'twice': (curses.ACS_BLOCK, _color_pair['progress-twice']),
                      }
        # width+1 to avoid wrapping the last
        # character.
        self.window = parent.derwin(1, width+1, row, column)
        self.width = width

    def set_progress(self, percentage):
        """Set the current progress reading.

        I actually have two stages, percentages from 1.0 to 2.0 render
        as a \"second stage\" in another color.

        @type percentage: float
        @param percentage: Current progress, in [0.0, 2.0]
        """

        fractional = math.fmod(percentage, 1.0)

        if (percentage > 0) and (fractional == 0):
            fractional = 1.0

        filled = int(fractional * self.width)
        empty = self.width - filled

        if percentage > 1.0:
            emptychar = self.chars['once']
            fillchar = self.chars['twice']
        else:
            emptychar = self.chars['none']
            fillchar = self.chars['once']

        for i in xrange(filled):
            self.window.addch(0, i, fillchar[0], fillchar[1])

        for i in xrange(filled, filled + empty):
            try:
                self.window.addch(0, i, emptychar[0], emptychar[1])
            except:
                print self.window
                print self.window.getmaxyx()
                print "f: %s e: %s" % (filled,
                                       empty)
                print "%s/%s" % (i, self.width)
                raise

        # draw me
        self.window.nooutrefresh()


class StatusWin:
    """I display general (not device-specific) status messages.
    """
    def __init__(self):
        height = 10
        width = 80
        self.win = curses.newwin(height, width, 14, 0)
        #       self.winBox.box()
        #       self.win = self.winBox.subwin(height-2, width-2, 1, 1)
        self.win.scrollok(1)

    def meminfo(self):
        if meminfo:
            self.msg(meminfo.meminfo_string())

    def msg(self, *a):
        """Write a message to the window.

        Does not add a trailing newline.
        """
        self.win.addstr(string.join(a, ' '))
        self.win.refresh()

    def readKey(self):
        """Read and return a single keystroke."""
        return curses.keyname(self.win.getch())

    def ask_yesno(self, prompt=None, default=False):
        """Ask a yes or no question.

        You may provide a prompt and a default answer.
        """
        if prompt:
            self.msg(prompt)
        reply = self.readKey()
        self.msg(reply)
        if default:
            if string.upper(reply) == "N":
                return False
            else:
                return default
        else:
            if string.upper(reply) == "Y":
                return True
            else:
                return default


def init_colorpairs():
    """Initialize curses color pairs.

    from the list of tuples L{pairdefs}.
    """
    pairnum = _FIRST_PAIR_NUMBER
    for label, attr, fg, bg in pairdefs:
        curses.init_pair(pairnum, fg, bg)
        _color_pair[label] = curses.color_pair(pairnum) | attr
        pairnum += 1


USE_SYSLOG_FOR_KLOG = True
def main(stdscr, devs):
    """Do the scanning, with nice ncurses windows and such.

    Start badblocks procs on the given devices, with widgets for each.

    stdscr is a curses window to operate in, such as that given to us
    by curses.wrapper.
    """
    if len(filter(lambda dev: dev.further_tests_needed(), devs)) == 0:
        return
    init_colorpairs()
    statusWin = StatusWin()
    disk.set_msg_function(statusWin.msg)
    msg = statusWin.msg

    # I had two ideas for reading the kernel messages.  One is to read
    # them from where they're spooled on disk by syslogd, the other
    # was to read them directly from a klogd process.
    if USE_SYSLOG_FOR_KLOG:
        try:
            klog = open(KLOG_PIPE, 'r')
            pyutil.makeNonBlocking(klog.fileno())

            # When we first run the program, klog messages from boot
            # get reported unnecesarily.  Flush 'em.
            klog.read()

        except IOError, e:
            msg("Failed to open klog pipe (%s), some errors may be missed.\n" % (str(e),))
            klog = None
    else:
        klog = klogd.KernelLog().fromchild.fileno()

    tests = badblocks.parallelTest(devs)

    # XXX: Find the terminal width instead of assuming it's 80 column.
    width = 80 / len(tests)
    column = 0
    for t in tests:
        BadblocksWidget(t, column=column, width=width)
        column = column + width
    if VERBOSE:
        statusWin.msg("num_blocks set to %d\n" % (badblocks.Badblocks.num_blocks,))
    statusWin.msg("Commencing scan.\n")
    badblocks.mainloop(tests, klog)

def run(devs):
    envprefix = "DISK_"
    l = filter(lambda item, s=envprefix: item[0][:len(s)] == s,
               os.environ.items())

    envopts = {}
    for key, value in l:
        envopts[key[len(envprefix):]] = value

    global VERBOSE
    if envopts.has_key("VERBOSE"):
        VERBOSE = True

    global MEMINFO_SPAM
    if envopts.has_key("MEMSPAM"):
        MEMINFO_SPAM = True

    curses.wrapper(main, devs)
