# -*- Python -*-
# $Id$

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
import diskdiag

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
SMARTCTL = "/usr/sbin/smartctl"

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


class QuestionablePartitionException(Exception):
    """Gets raised when we find a partition we don't know what to with.

    args should be a list of (partition, type) tuples.
    """
    pass

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


def list_block_controllers():
    """Wrapper around /proc/devices.

    @returns: short names of all controllers of block devices in the
        system which Linux knows about, e.g. ['fd', 'ide0', 'ide1']
    @returntype: list of strings
    """
    block = False
    proc_devices_f = open("/proc/devices")
    controllers = []
    try:
        for l in proc_devices_f.readlines():
            l = string.strip(l)
            if l == "Block devices:":
                block = True
                continue
            if block:
                major, name = string.split(l, None, 1)
                controllers.append(name)
    finally:
        proc_devices_f.close()

    return controllers

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

    #drives = filter(is_not_mounted, drives)
    drives.sort()
    return map(lambda d: diskdiag.DiskDevice(d), drives)

_sfdisk_re = re.compile("^(?P<device>/dev/\S*?)\s*: start=\s*(?P<start>\d*), "
                        "size=\s*(?P<size>\d*), "
                        "Id=\s*(?P<id>[0123456789abcdef]+)")


def list_partitions(drive, doIncludeEmpty=True):
    """What partitions are on this drive?

    @returns: a tuple (I{device}, I{start}, I{length}, I{id}),
        where I{device} is a string of the absolute pathname of the device,
        I{start} and I{length} are sector counts,
        and I{id} is an integer identifying the partition type.
    """
    # -uS units in sectors
    partitions = []
    cmd = "%(sfdisk)s -uS --dump %(drive)s" % {'sfdisk':SFDISK,
                                               'drive':drive}

    sfdisk_out, sfdisk_in, sfdisk_err = popen2.popen3(cmd)

    try:
        for l in sfdisk_out.readlines():
            m = _sfdisk_re.match(l)
            if m:
                d = m.groupdict()
                if doIncludeEmpty or (long(d['size']) != 0):
                    partitions.append((d['device'], long(d['start']),
                                       long(d['size']), int(d['id'], 16),))
    finally:
        # capture all messages but don't do anything for now
        ecode = sfdisk_in.close()
        errmsg = sfdisk_err.read()
        outmsg = sfdisk_out.read()
        # msg("\nsfdisk list partition exit code:", ecode)
        # msg("\nsfdisk list partition error:", errmsg, ":error")
        # msg("\nsfdisk list partition out:", outmsg, ":out")

    return partitions

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


def supported_modes(blockDevice):
    """Return the supported PIO and DMA modes for an IDE device.

    This is a hdparm wrapper.
    """
    cmd = "%(hdparm)s -i %(dev)s" % {'hdparm': HDPARM,
                                     'dev': blockDevice}
    hdparm = os.popen(cmd)

    modes = {}
    try:
        for l in hdparm.readlines():
            if string.find(l, 'modes:') != -1:
                kind, these_modes = string.split(l, ':', 1)
                these_modes = string.split(these_modes)
                kind = string.split(kind)[0]
                modes[kind] = these_modes
    finally:
        exitcode = hdparm.close()
        if exitcode:
            raise RuntimeError("hdparm returned error code %s" % (exitcode,))

    return modes

def mke2fs(device):
    """mke2fs wrapper

    Note: this blocks until it's done.  I forget how slow mke2fs is --
    is this a bad idea?

    Example: mke2fs(\"/dev/hdc1\")
    """
    cmd = "%(mke2fs)s -q %(dev)s" % {'mke2fs': MKE2FS,
                                     'dev': device}
    p = popen2.Popen4(cmd)
    ecode = p.wait()
    if ecode:
        # XXX: This is a crappy exception type.  Make a more specific/
        # recognizeable one.  And collect stderr output so they know
        # what went wrong.
        raise RuntimeError("mke2fs failed with exit code %s" % (ecode,))
    return

def size_string(bytes):
    """Given a number of bytes, returns a metric string description.

    i.e. 9000000000 bytes is \"8.38 GB\"
    """

    if bytes >= (2 ** (10+10+10)):
        return "%.2f GB" % (bytes / (2.0 ** (10+10+10)),)
    elif bytes >= (2 ** (10+10)):
        return "%.2f MB" % (bytes / (2.0 ** (10+10)),)
    elif bytes >= (2 ** 10):
        return "%.2f kB" % (bytes / (2.0 ** 10),)
    else:
        return "%d bytes" % (bytes,)


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


if __name__ == "__main__":
    drives = findSysDevicesToScan()
    print drives.join(", ")
