# -*- Python -*-
# $Id$

"""Wrapper for badblocks.

badblocks is searches a device for bad blocks.
It's shipped with e2fsprogs.
See badblocks(8).
"""

# floppies use mbadblocks
# and setfdparm

# Give the badblocks machine plenty of memory.

BADBLOCKS="badblocks"

import errno, os, popen2, string, re, select, time, types

# sibling import
import disk
from fgdiag.lib import pyutil

True = (1==1)
False = not True

### Messages:
#       Writing Pattern %(pattern)s:
#       Reading and Comparing:
#
#       Checking for bad blocks (non-destructive read-write test):
#
#       ?

class _Accessor:
    def __setattr__(self, key, value):
        method = getattr(self, "set_%s" % (key,), None)
        if method:
            method(value)
        else:
            self._reallySet(key, value)

    def _reallySet(self, key, value):
        self.__dict__[key] = value


unbackspace_re = re.compile("\x08+")

class Badblocks(popen2.Popen3, _Accessor):
    KMSG_COUNT_TOLERANCE = 1
    BAD_SECTOR_COUNT_TOLERANCE = 1
    kmsg_count = 0

    path = BADBLOCKS
    num_blocks = 1024 # XXX: ??? what should this be set to?
    modeFlag = None
    runningCount = 0
    totalSumCount = None
    passes = 1
    KEEP_LOGFILE = False

    # badblocks flags:
    #  -c num_blocks: Test this many at once.  (This is why we want RAM.)
    #  -p num_passes: This many *good* passes must happen before exiting. (default 0)
    #  -s : show progress
    #  -v : verbose
    #  -w : write-mode testing; destroys data!

    def __init__(self, device, num_blocks=None):
        self.observers = []
        self.sectorCount = disk.getDeviceSize(device) / 1024
        self.totalSumCount = self.sectorCount * self.passes
        if num_blocks is not None:
            self.num_blocks = num_blocks

        self.startTimes = [time.time()]

        cmd = "%(badblocks)s -c %(num_blocks)s -s %(mode)s %(dev)s" % {
            'badblocks': self.path,
            'num_blocks': self.num_blocks,
            'mode': self.modeFlag,
            'dev': device,
            }
        popen2.Popen3.__init__(self, cmd, True)
        pyutil.makeNonBlocking(self.fromchild.fileno())
        pyutil.makeNonBlocking(self.childerr.fileno())

        self.device = device
        self.drive = string.split(device, '/')[-1][:3]
        self._parserState = "stage"
        self.badlist = []

        if self.KEEP_LOGFILE:
            self.logfile = open("/tmp/bb.%s.log" % (self.device[-3:],), "a")

    def addObserver(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)
        observer.set_blockDevice(self.device)
        observer.set_testMode(self.modeFlag)
        if self.totalSumCount:
            observer.set_totalSumCount(self.totalSumCount)

        return self

    def progress(self, numerator, denominator):
        for o in self.observers:
            o.progress(numerator, denominator)

    def set_runningCount(self, value):
        self._reallySet("runningCount", value)

        for o in self.observers:
            o.set_runningCount(value)

    def set_totalSumCount(self, value):
        self._reallySet("totalSumCount", value)

        for o in self.observers:
            o.set_totalSumCount(value)

    def set_operation(self, op):
        self._reallySet("operation", op)
        for o in self.observers:
            o.set_operation(op)

    def finished(self, exit_code):
        """Called when the badblocks process terminates.
        """
        for o in self.observers:
            o.finished(exit_code)

    ### select callbacks

    def gotOutput(self):
        output = self.fromchild.read()

        lines = string.split(output, "\n")
        for l in lines:
            if not l:
                continue
            try:
                sector = int(string.strip(l))
                self.badlist.append(sector)
                for o in self.observers:
                    o.foundBadblock(sector)

                if len(self.badlist) >= self.BAD_SECTOR_COUNT_TOLERANCE:
                    self.terminate()

            except ValueError, e:
                raise ValueError("Got _%s_ on stdout" % (repr(output),))

    def gotError(self, s=None):
        if s is None:
            output = self.childerr.read()
        else:
            output = s

        if self.KEEP_LOGFILE:
            self.logfile.write(output)

        lines = string.split(unbackspace_re.sub('\n', output), '\n')
        for l in lines:
            method = getattr(self, "read_%s" % (self._parserState,))
            if l:
                try:
                    method(l)
                except RuntimeError, exc:
                    o, e = None, None
                    try:
                        o = self.fromchild.read()
                    except IOError:
                        pass
                    try:
                        e = self.childerr.read()
                    except IOError:
                        pass

                    raise RuntimeError("%s %s\n E: %s\nO: %s\n" % (self.device,
                                                                   exc.args[0],
                                                                   o, e))

    def klog(self, msg):
        self.kmsg_count += 1
        for o in self.observers:
            o.klog(msg)
        if self.kmsg_count >= self.KMSG_COUNT_TOLERANCE:
            self.terminate()

    ### handlers for parsing badblocks output

    def read_stage(self, output):
        # Most tests have only one stage.
        self._parserState = "progress"

    def read_progress(self, output):
        if not output:
            return
        elif string.strip(output) == "done":
            self._parserState = "done"
            return

        try:
            numerator, denominator = map(string.strip, string.split(output, "/"))
            numerator, denominator = map(long, [numerator, denominator])
        except ValueError, e:
            raise ValueError("Progress read error on _%r_\n%s"
                             % (output, e.args[0]))

        self.progress(numerator, denominator)
        if numerator == denominator:
            self._status = "done"

    def read_done(self, output):
        pass # print "%s done: %s" % (self, output)


    ### Popen3 subclassing

    def poll(self):
        val = popen2.Popen3.poll(self)
        if val != -1:
            self.finished(val)
        return val

    ### accessors to Popen3

    def get_out(self):
        return self.fromchild

    def get_err(self):
        return self.childerr

    def get_dev(self):
        return self.device

    def terminate(self):
        # Signal 15: SIGTERM
        try:
            os.kill(self.pid, 15)
        except OSError, e:
            if e.errno == errno.ESRCH:
                # No such process (it already died)
                pass
            else:
                raise

    def __str__(self):
        s = "<%s at %x scanning %s>" % (self.__class__, id(self), self.device)
        return s


class BadblocksRead(Badblocks):
    modeLabel = "read-only"
    modeFlag = ""

    def progress(self, numerator, denominator):
        Badblocks.progress(self, numerator, denominator)

    def read_stage(self, output):
        self.operation = "Reading"
        Badblocks.read_stage(self, output)


### Write patterns:
#       0xaaaaaaaa
#       0x55555555
#       0xffffffff
#       0x00000000

class BadblocksWrite(Badblocks):
    modeLabel = "overwrite & read"
    modeFlag = "-w"
    operation = None
    widget = None
    pattern = None
    # Four write passes, four read passes.
    passes = 8

    def progress(self, numerator, denominator):
        Badblocks.progress(self, numerator, denominator)

    def read_stage(self, output):
        Badblocks.read_stage(self, output)

        if (self.operation is "Reading") or (not self.operation):
            self.operation = "Writing"
            match = writing_re.search(output)
            if match:
                self.pattern = match.groupdict()["pattern"]
            else:
                raise RuntimeError("'Writing' string didn't match: %r" %
                                   (output,))
        else:
            # XXX: Sanity check here.
            self.operation = "Reading"
        remainder = string.split(output, ":", 1)
        if (len(remainder) > 1) and ('/' in remainder[-1]):
            self.gotError(remainder[-1])

    def set_pattern(self, pattern):
        self._reallySet("pattern", pattern)
        for o in self.observers:
            o.set_pattern(pattern)

    def read_progress(self, output):
        # The badblocks status indicicator backspaces over itself.
        output = string.replace(output,"\x08","")
        if not output:
            return
        elif string.strip(output) == "done":
            self.runningCount = self.runningCount + self.sectorCount
            if (self.operation == "Reading") and (self.pattern == "0x00000000"):
                # That was the last pass.
                self._parserState = "done"
            else:
                self._parserState = "stage"
            return

        try:
            numerator, denominator = map(string.strip, output.split("/"))
        except ValueError, exc:
            exc.args = exc.args + (output,)
            # print "ERR: %r" % (output,)
            raise exc

        try:
            numerator, denominator = map(long, [numerator, denominator])
        except ValueError, e:
            raise ValueError, "ERR: _%r_ / _%r_" % (numerator, denominator)
        self.progress(numerator, denominator)

        if numerator == denominator:
            if self.pattern == "0x00000000":
                self._status = "done"
            else:
                self.stage = "stage"

    def finished(self, exit_code):
        """Called when the badblocks process terminates.
        """
        self.pattern = None
        Badblocks.finished(self, exit_code)

writing_re = re.compile(r"^Writing pattern (?P<pattern>0x\S{8})")


class BadblocksWriteSafely(Badblocks):
    modeLabel = "safe write & read"
    stage = None
    pattern = None
    modeFlag = "-n"

    def __init__(self, device):
        Badblocks.__init__(self, device)
        self.totalSumCount = self.sectorCount

    def read_stage(self, output):
        self.operation = "WriteSafely"
        Badblocks.read_stage(self, output)

    def progress(self, numerator, denominator):
        if not self.totalSumCount:
            self.totalSumCount = self.sectorCount = denominator
        Badblocks.progress(self, numerator, denominator)

bb_classes = {
    'read-only': BadblocksRead,
    'over-write': BadblocksWrite,
    'safe-write': BadblocksWriteSafely,
    }


def start_badblocks(device, mode):
    """Constructor for Badblocks objects.

    @param device: The absolute pathname of the device to run badblocks on.
    @type device: string
    @param mode: one of C{'read-only'}, C{'over-write'}, or C{'safe-write'}.
    @type mode: string
    """
    return bb_classes[mode](device)


class BadblocksObserver(_Accessor):
    pattern = None
    operation = None
    runningCount = 0
    totalSumCount = None
    _observed = None

    def set_testMode(self, testMode):
        """Define which test mode badblocks is running.
        """

    def set_blockDevice(self, blockDevice):
        """Called to specify what block device is being tested.
        """

    def set_operation(self, op):
        """Called when the test's current operation changes.

        'Reading' or 'Writing'
        """

    def set_pattern(self, pattern):
        """Called when the current testing pattern changes.

        Only used for the 'over-write' test type.
        """

    def set_runningCount(self, count):
        """Called to update the number of sectors tested in completed passes.
        """

    def set_totalSumCount(self, total):
        """Called to define the total number of sectors visited in all passes.
        """

    def progress(self, numerator, denominator):
        """Called to update the progress of the current test pass.
        """

    def foundBadblock(self, sector):
        """Called when a bad block is found.
        """

    def finished(self, exit_code):
        """Called when the badblocks process terminates.
        """

    def klog(self, msg):
        """Called when klog talks about a device I'm working with.
        """

def parallelTest(deviceList):
    """Test a number of devices in parallel.

    @param deviceList: Devices to scan.
    @type deviceList: A list of (I{device}, I{scanmode}) pairs, where
        I{device} is a string containing the absolute pathname of the
        device, and I{scanmode} is one of C{'read-only'}, C{'over-write'},
        or C{'safe-write'}.

        An element of this list may also be a list of (I{device},
        I{scanmode}) pairs itself, in which case that element is taken
        as a list of devices to test in serial.  This serial test will
        be conducted in parallel with the others.

    @returntype: list of L{Badblocks} and L{SerialTest}s
    """

    badblockses = []
    try:
        for i in deviceList:
            if isinstance(i[0], types.StringType):
                dev, mode = i
                badblockses.append(start_badblocks(dev, mode))
            else:
                # Assume it's a sequence to be tested in serial.
                badblockses.append(SerialTest(i))
    except ValueError, e:
        raise ValueError(e.args[0] + repr(deviceList))

    return badblockses


class SerialTest:
    """Iterator performs tests in serial.
    """

    pos = 0
    current = None

    def __init__(self, deviceList):
        self.queue = deviceList
        self.results = []

        total = 0
        for dev, mode in deviceList:
            total = total + (disk.getDeviceSize(dev) / 1024) * bb_classes[mode].passes

        self.totalSumCount = total

        self.next()

    def next(self):
        if self.pos >= len(self.queue):
            return None

        if self.current:
            observers = self.current.observers
            self.runningCount = self.runningCount + self.current.sectorCount
        else:
            observers = []

        self.current = apply(start_badblocks, self.queue[self.pos])
        self.current.totalSumCount = self.totalSumCount
        self.current.runningCount = self.runningCount

        self.pos = self.pos + 1

        for o in observers:
            self.current.addObserver(o)

        return self.current

    def poll(self):
        val = self.current.poll()
        if val != -1:
            if self.next():
                return -1
        return val

    def __getattr__(self, key):
        return getattr(self.current, key)

# this list will be populated by the observing class(es)
mainloop_hooks = []

def mainloop(badblockses, klog=None):
    """Mainloop; reads output from badblocks and syslog.

    I also catch KeyboardInterrupt, sending termination signals to any
    child processes.
    """

    try:
        _mainloop(badblockses, klog)
    except KeyboardInterrupt:
        for b in badblockses:
            b.terminate()
        disk.msg("Ctrl-C caught, shutting down.\n")
        # go back into the loop for a bit and let things die gracefully.
        _mainloop(badblockses, klog)
    except:
        for b in badblockses:
            try:
                b.terminate()
            except:
                pass
        raise

def _mainloop(badblockses, klog=None):
    """The real mainloop."""
    outputs = {}
    errors = {}
    # wrap the klog file description in a list, for select's benefit.
    klog_list = []
    if klog:
        klog_list.append(klog)
        logstuff = ''

    while badblockses:
        for hook in mainloop_hooks:
            hook()
        outputs.clear()
        errors.clear()

        for b in badblockses:
            out, err = b.get_out(), b.get_err()
            if out is not None:
                outputs[out] = b
            if err is not None:
                errors[err] = b

        readme = select.select(outputs.keys() + errors.keys() + klog_list,
                               [], [])[0]

        if klog in readme:
            readme.remove(klog)
            logstuff = logstuff + klog.read()
            for l in string.split(logstuff,'\n')[:-1]:
                if not l:
                    continue
                kmsg = disk.take_syslog_line(l)
                if kmsg:
                    if kmsg is disk._OLD_MESSAGE:
                        continue

                    for b in badblockses:
                        if b.drive == kmsg['drive']:
                            b.klog(kmsg)
                else:
                    disk.msg(l + '\n')
            # Any leftover fraction of a line is saved for next pass.
            logstuff = string.split(logstuff, '\n')[-1]

        active_processes = {}
        for f in readme:
            if outputs.has_key(f):
                process = outputs[f]
                process.gotOutput()
                active_processes[process] = 'Set'

            if errors.has_key(f):
                process = errors[f]
                process.gotError()
                active_processes[process] = 'Set'

        for p in active_processes.keys():
            exit_code = p.poll()
            if exit_code == -1:
                continue
            else:
                badblockses.remove(p)
