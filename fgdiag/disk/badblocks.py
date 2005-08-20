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
    """A badblocks process.

    Runs the unix badblocks(8) utility.

    @param device: The device I am checking.
    @type device: diskdiag.DiskDevice
    """
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
        """Start a new badblocks process.

        @param device: The device to check.
        @type device: diskdiag.DiskDevice

        @param num_blocks: the -c paramater to badblocks, \"the number of
            blocks which are tested at a time.\"
            Defaults to L{Badblocks.num_blocks}.
        @type num_blocks: int
        """
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
            'dev': device.dev,
            }
        popen2.Popen3.__init__(self, cmd, True)
        pyutil.makeNonBlocking(self.fromchild.fileno())
        pyutil.makeNonBlocking(self.childerr.fileno())

        self.device = device
        self.drive = string.split(device.dev, '/')[-1][:3]
        self._parserState = "stage"
        self.badlist = []

        if self.KEEP_LOGFILE:
            self.logfile = open("/tmp/bb.%s.log" % (self.device.dev[-3:],), "a")

    def addObserver(self, observer):
        if observer not in self.observers:
            self.observers.append(observer)
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

                    raise RuntimeError("%s %s\n E: %s\nO: %s\n" % (self.device.dev,
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
        s = "<%s at %x scanning %s>" % (self.__class__, id(self), self.device.dev)
        return s

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
            if (self.operation == "Reading") and (self.pattern == "03x00000000"):
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

writing_re = re.compile(r"^Testing with pattern (?P<pattern>0x\S{0,2})")


def start_badblocks(device):
    """Constructor for Badblocks objects.

    @param device: A diskdiag.DiskDevice object.
    """
    return BadblocksWrite(device)


class BadblocksObserver(_Accessor):
    pattern = None
    operation = None
    runningCount = 0
    totalSumCount = None
    _observed = None

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
    @type deviceList: A list of diskdiag.DiskDevice objects.

    @returntype: list of L{Badblocks}s
    """

    badblockses = []
    try:
        for i in deviceList:
            badblockses.append(start_badblocks(i))
    except ValueError, e:
        raise ValueError(e.args[0] + repr(deviceList))

    return badblockses


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
