#!/usr/bin/env python
# $Id$

"""Curses front-end to disk testing module.

@var MINIMUM_SIZE: Do not recommend testing disks with fewer than this many
    bytes.
"""

__version__ = '$Revision$'[11:-2]

import curses, math, os, string, sys, time
try:
    from mx import DateTime
except ImportError:
    import DateTime

# sibling import
import disk, badblocks # , klogd
from fgdiag.lib import pyutil

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

allDrives = {}

class BadblocksWidget(badblocks.BadblocksObserver):
    """I am the visual representation of the running BadBlocks.
    """
    PHASE_ROW = 5
    TOP = 1
    BOTTOM = 3
    PROGRESS1_ROW = BOTTOM
    PROGRESS2_ROW = TOP
    SUMMARY_ROW = 0
    pattern = ""
    blockDevice = None

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

        w.nooutrefresh()

    def set_blockDevice(self, blockDevice, description=None):
        """Called to set the label identifying the device being processed.

        blockDevice is a String such as \"hda\".
        """
        self.dev = blockDevice
        # XXX: sloppy
        if string.find(blockDevice, 'hdb') != -1:
            channel = "secondary"
        else:
            channel = "primary"
        self.border.attrset(_color_pair["%s-border" % (channel,)])
        self.border.box()
        self.border.addstr(0, 1, blockDevice,
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
        isGood = True

        # if the badblocks process exited with an exitCode of 0, then it died naturally
        if not exitCode:
            self.msgwin.addstr("%s of %s complete:\n" % (self._observed.modeLabel,
                                                         self._observed.device))
            seconds_elapsed = time.time() - self._observed.startTimes[0]
            megabytes = (disk.getDeviceSize(self._observed.device) /
                         (2.0 ** (10+10)))
            self.msgwin.addstr("%s elapsed, %s per hundred megabytes.\n" % (
                str(DateTime.TimeDelta(seconds = seconds_elapsed)),
                str(DateTime.TimeDelta(seconds = seconds_elapsed /
                                       (megabytes / 100.0)))))
        else:
            self.msgwin.addstr("The badblocks process was killed.\n")
            isGood = False

        if self._observed.badlist:
            self.msgwin.addstr("%d bad sectors found. :(\n" % (len(self._observed.badlist),))
            isGood = False

        if isGood:
            self.msgwin.addstr("PASSED", _color_pair['success'])
            self.progress(self._observed.sectorCount, self._observed.sectorCount)

        allDrives[self.dev]["isGood"] = isGood

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


USE_SYSLOG_FOR_KLOG = 1
def main(stdscr):
    """Ready, set, go!

    Look for drives, prompt about them, start things running and
    display badblocks widgets for all of them...  The whole shebang.

    stdscr is a curses window to operate in, such as that given to us
    by curses.wrapper.
    """
    init_colorpairs()
    statusWin = StatusWin()
    disk.set_msg_function(statusWin.msg)
    msg = statusWin.msg

    if MEMINFO_SPAM:
        badblocks.mainloop_hooks.insert(0, statusWin.meminfo)

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


    # XXX: Provide a real command-line interface.
    if sys.argv[1:]:
        msg("Got argv", str(sys.argv[1:])+"\n")
        badblockses = badblocks.parallelTest([(sys.argv[1], 'over-write')])
    else:

        msg("I will perform the following scans:\n")
        devs = None
        try:
            devs = disk.findBlockDevicesToScan()
        except disk.QuestionablePartitionException, qps:
            msg("I found partition(s) with which I do not know what to do:\n")
            for part in qps.args[0]:
                # part is (dev, type)
                msg("%s: type 0x%02x\n" % part)
            if not statusWin.ask_yesno("Should I clobber them anyway? [y/N] "):
                msg("Not clobbering. Put this on the weird drives pile.")
                return 0
            msg("I will perform the following scans:\n")
            devs = disk.findBlockDevicesToScan(forceClobber=True)

        if not devs:
            msg("I did not find any drives to scan.")
            return 0

        for d, mode in devs:
            idstuff = disk.identification(d)
            if VERBOSE:
                model = "%s SN#%s" % (idstuff['model'],
                                      idstuff['serialNo'])
            else:
                model = idstuff['model']

            size = disk.getDeviceSize(d)
            size_str = disk.size_string(size)
            if size < MINIMUM_SIZE:
                size_str += " (small)"
            msg("    %s - %s, %s\n" % (d,
                                       model,
                                       size_str))

            global allDrives
            allDrives[d] = {}
            allDrives[d].update(idstuff)
            allDrives[d]["size"] = size_str
            
            if VERBOSE:
                for kind, modes in disk.supported_modes(d).items():
                    msg("%s: %s\n" % (kind, string.join(modes)))
        msg("\n")

        if not statusWin.ask_yesno("Okay? [y/N] "):
            msg("\nIn that case, I won't do it.\n")
            return 0
        else:
            msg("\n")

        badblockses = badblocks.parallelTest(devs)

    # XXX: Find the terminal width instead of assuming it's 80 column.
    width = 80 / len(badblockses)
    column = 0
    for b in badblockses:
        BadblocksWidget(b, column=column, width=width)
        column = column + width
    if VERBOSE:
        statusWin.msg("num_blocks set to %d\n" % (badblocks.Badblocks.num_blocks,))
    statusWin.msg("Commencing scan.\n")
    badblocks.mainloop(badblockses, klog)
    for drv, attrs in allDrives.items():
        stat = "FAILED"
        if attrs["isGood"]:
            stat = "PASSED"
        msg("%(drive)s %(stat)s %(size)s" % {
            "drive": drv,
            "stat": stat,
            "size": attrs["size"],
            })
    return 0

def wrapper():
    curses.wrapper(main)

def run():
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

    wrapper()

if __name__ == '__main__':
    run()
