# -*- Python -*-

"""An interface to a variety of disk-related utilities.

@var BADBLOCKS: The name of the system I{badblocks} command.
@type BADBLOCKS: string
@var HDPARM: The name of the system I{hdparm} command.
@type HDPARM: string
@var RDEV: The name of the system I{rdev} command.
@type RDEV: string
@var SFDISK: The name of the system I{sfdisk} command.
@type SFDISK: string

@var doWipe: Partition types to write over indiscriminately.
    See also L{noWipe}.  Keys are numeric partition types, values are
    human-readable strings.
@type doWipe: dict

@var noWipe: Partition types to perform read-only tests on.
    See also L{doWipe}.  Keys are numeric partition types, values are
    human-readable strings.

@type noWipe: dict
"""

import StringIO
import operator, os, popen2, string, re, sys, time
from subprocess import call, Popen
import diskdiag
from fgdiag.lib import userinteraction as ui

True = (1==1)
False = not True

# This token indicates that the message was from before the module was imported.
_OLD_MESSAGE = "old message"
_startup_time = time.localtime(time.time())

# paths of external utilities.
BADBLOCKS = "badblocks"
HDPARM = "/sbin/hdparm"
RDEV = "rdev"
SFDISK = "/sbin/sfdisk"

# XXX: If things continue to work with this disabled, remove the
# timestamp-check code entirely.  Otherwise, set back to True.
_CHECK_TIMESTAMPS = False

def default_msg(*a):
    """Because 'print' isn't a function.

    Note that I don't include a trailing newline.
    """
    sys.stdout.write(string.join(a, ' '))

msg = default_msg

def set_msg_function(f):
    """Provide a callable to use as the generic message display function.
    """
    global msg
    if not operator.isCallable(f):
        raise TypeError, "%s is not a callable object." % (f,)
    msg = f


def list_mounted_devices():
    """List devices which are mounted or being used as swap.

    @returns: absolute pathnames of devices, e.g. \"/dev/hdb1\"
    @returntype: list of strings
    """
    devices  = []
    mounted_f = open("/proc/mounts")
    try:
        for l in mounted_f.readlines():
            device, mountpoint, fstype, options, foo, bar = string.split(l)
            if device[:5] == "/dev/":
                if device == "/dev/root" and mountpoint == "/":
                    device, mountpoint = string.split(os.popen(RDEV).read())
                devices.append(device)
    finally:
        mounted_f.close()

    swap_f = open("/proc/swaps")
    try:
        for l in swap_f.readlines():
            if l[:5] == "/dev/":
                devices.append(string.split(l)[0])
    finally:
        swap_f.close()
    return devices

_drive_re = re.compile("^[sh]d.$")
def findSysDevicesToScan():
    """Returns a list of non-removable, unmounted block devices. """
    possible = os.listdir("/sys/block")
    actual = []
    for entry in possible:
        if _drive_re.search(entry):
            removable = open("/sys/block/%s/removable" % (entry)).read()[0]
            if removable == '0':
                actual.append("/dev/%s" % (entry))
    return clean_drives_list(actual)

def clean_drives_list(drives):
    mounted = list_mounted_devices()
    def is_not_mounted(drive, mounted=mounted):
        l = len(drive)
        for d in mounted:
            if d[:l] == drive:
                return False
        return True

    drives = filter(is_not_mounted, drives)
    drives.sort()
    drives = map(lambda d: diskdiag.DiskDevice(d), drives)
    for drive in drives:
        drive.get_data()
    return drives

_sfdisk_re = re.compile("^(?P<device>/dev/\S*?)\s*: start=\s*(?P<start>\d*), "
                        "size=\s*(?P<size>\d*), "
                        "Id=\s*(?P<id>[0123456789abcdef]+)")

def getDeviceSize(blockDevice):
    """Given a device name, return the size of the device in bytes.
    """
    cmd = "%(sfdisk)s --show-size %(dev)s" % {'sfdisk': SFDISK,
                                              'dev': blockDevice}
    sfdisk = os.popen(cmd)

    try:
        outstr = string.strip(sfdisk.read())
    finally:
        exitcode = sfdisk.close()
        if exitcode:
            raise RuntimeError("sfdisk returned error code %s" % (exitcode,))

    try:
        size = long(outstr) * 1024
    except ValueError, e:
        raise ValueError("Can't make this look like a device size: %s"
                         % (outstr,))
    return size

def identification(blockDevice):
    """Return a dictionary containing the serial number and model identifier.
    """
    d_ = string.split(blockDevice, '/')[-1]
    f = open("/proc/ide/%s/identify" % (d_,))
    o = StringIO.StringIO()
    for l in f.xreadlines():
        for word in string.split(l):
            for byte in (word[0:2], word[2:4]):
                o.write(chr(int(byte, 16)))

    o.seek(0)
    s = o.read()

    f.close()
    o.close()
    return {'serialNo': string.strip(s[20:40]),
            'model': string.strip(s[54:94])}
##Kysle
def ScsiIdentification(blockDevice):
    """Return a dictionary containing the serial number and model identifier.
    """

    id_re = re.compile("Attached scsi disk " + blockDevice.strip('/dev/') + " at")
    blockDevice_id = filter(id_re.search, open("/var/log/dmesg").readlines())
    pattern = re.compile(',')
    blockDevice_id = pattern.sub("", blockDevice_id[0])
    blockDevice_id = blockDevice_id.split()[9]

    blockDevice_ident_re = re.compile("\(scsi0:A:" + blockDevice_id + "\):.*\n(.*)\n")
    blockDevice_ident = open("/var/log/dmesg").read()
    match = blockDevice_ident_re.search(blockDevice_ident).groups()[0]

    return {'serialNo': match.split()[3],
            'model': match.split()[1]}

######################################################
# EXCERPTS FROM syslog log file:
# Dec 27 16:46:16 progeny kernel: hdd: read_intr: status=0x59 { DriveReady SeekComplete DataRequest Error }
# Dec 27 16:46:16 progeny kernel: hdd: read_intr: error=0x40 { UncorrectableError }, LBAsect=56770, sector=48704
# Dec 27 16:46:16 progeny kernel: end_request: I/O error, dev 16:43 (hdd), sector 48704
# Dec 27 16:49:05 progeny kernel: hdd: read_intr: status=0x59 { DriveReady SeekComplete DataRequest Error }
# Dec 27 16:49:05 progeny kernel: hdd: read_intr: error=0x40 { UncorrectableError }, LBAsect=104321, sector=96254
# Dec 27 16:49:05 progeny kernel: end_request: I/O error, dev 16:43 (hdd), sector 96254


# Parse stuff from ide.c:ide_dump_status()
_syslog_stamp = re.compile(
    # date may be left-padded
    r'^(?P<month>\w+) {,2}(?P<day>\d+) '
    r'(?P<time>\d\d:\d\d:\d\d) '
    r'(?P<hostname>\S+) ')

_is_kernel = re.compile(r'kernel: ')

# XXX: the 'drives' list is faked here.
_ide_dump = re.compile(r'(?P<drive>%s)' %
                      string.join(map(lambda s: '(?:%s)' % (s,), ['hda','hdb','hdc','hdd'] or drives), '|')
                      + r': (?P<msg>.*?): ')

_ide_status_dump = re.compile(r'status=(?P<statcode>0x..) '
                             r'{ (?P<statwords>.*?) }$')

_ide_error_dump = re.compile(r'error=(?P<errcode>0x..) { (?P<errwords>.*?) }')
_lba_dump = re.compile(r', LBAsect=(?P<LBAsect>\d+)')
_chs_dump = re.compile(r', CHS=(?P<cyl>\d+)/(?P<head>\d+)/(?P<sect>\d+)')
_sector_dump = re.compile(r', sector=(?P<sector>\d+)$')

_end_request_error = re.compile(r'end_request: I/O error, '
                                r'dev (?P<devnum>\d+:\d+) '
                                r'\((?P<devname>\w+?)\), '
                                r'sector (?P<sector>\d+)$')

def take_syslog_line(line):
    """Given a line from syslog, return a dictionary of disk-relevant bits.

    If I return None, I did not recognize the message as being disk-related.
    """
    msg = {}

    match = _syslog_stamp.match(line)
    if match is None:
        raise ValueError, "Eek! How did we get this from syslog?\n%s\n" % (repr(line),)

    if _CHECK_TIMESTAMPS:
        datetimestamp = "%s %s %s" % (match.group("month"), match.group("day"),
                                      match.group("time"))
        syslog_time = time.strptime(datetimestamp,"%b %d %H:%M:%S")

        # compare the syslog time to the time we were started.
        # ignore the year b/c syslog doesn't include it
        if syslog_time[1:] < _startup_time[1:]:
            return _OLD_MESSAGE

    match = _is_kernel.match(line, match.end())
    if match is None:
        return None
    ide_match = _ide_dump.match(line, match.end())
    if ide_match is not None:
        match = ide_match
        msg.update(match.groupdict())

        status_match = _ide_status_dump.match(line, match.end())
        if status_match is not None:
            msg.update(status_match.groupdict())
            msg['statwords'] = string.split(msg['statwords'])
            return msg

        error_match = _ide_error_dump.match(line, match.end())
        if error_match is not None:
            msg.update(error_match.groupdict())
            msg['errwords'] = string.split(msg['errwords'])

            pukey_words = ('UncorrectableError', 'SectorIdNotFound', 'AddrMarkNotFound')
            if not filter(lambda w, p=pukey_words: w in p, msg['errwords']):
                # If none of those words were found, there won't be a sector
                # identification following.
                return msg

            lba_match = _lba_dump.match(line, error_match.end())
            if lba_match is not None:
                match = lba_match
                msg['LBAsect'] = long(match.group('LBAsect'))
            else:
                chs_match = _chs_dump.match(line, error_match.end())
                if chs_match is None:
                    # XXX: This shouldn't happen!
                    # Issuing a warning would be nice, but it shouldn't die.
                    pass
                else:
                    msg['CHS'] = tuple(map(long, (chs_match.group('cyl','head','sect'))))
                match = chs_match
            sector_match = _sector_dump.match(line, match.end())
            if sector_match is not None:
                msg['sector'] = long(sector_match.group('sector'))
            return msg

    endreq_match = _end_request_error.match(line, match.end())
    if endreq_match is not None:
        msg['sector'] = long(endreq_match.group('sector'))
        msg['drive'] = endreq_match.group('devname')
        msg['devnum'] = tuple(map(int, string.split(endreq_match.group('devnum'), ':')))
        msg.update(endreq_match.groupdict())

        return msg

    return None

def smart_test(devs):
    for dev in devs:
        if dev.further_tests_needed():
            ui.notice("Performing smart test on %s" % (dev))
            dev.smart_test()
            ui.notice("Smart test finished")
    failed = False
    for dev in devs:
        if not dev.further_tests_needed():
            ui.notice("%s has failed." % dev.dev)

def dd_wipe(devs):
    for wipe_type in ("zero", "urandom"):
        ui.notice("Wiping the data on the drives with %ss..." % (wipe_type))
        procs = []
        for dev in devs:
            if dev.further_tests_needed():
                procs.append(dev.dd_wipe(wipe_type))
        while( len(procs) > 0 ):
            call(["/bin/sleep", "10"])
            procs = filter(lambda proc: not proc.poll(), procs)
            call(["/sbin/kill", "-USR1", proc.pid])
        ui.notice("Data wipe finished.")

def install_os(devs):
    ui.notice("Installing operating systems...")
    procs = []
    for dev in devs:
        if dev.further_tests_needed():
            procs.append(dev.install_os())
    while( len(procs) > 0 ):
        call(["/bin/sleep", "10"])
        procs = filter(lambda proc: not proc.poll(), procs)
    ui.notice("Done installing.")

if __name__ == "__main__":
    drives = findSysDevicesToScan()
    print drives.join(", ")
