# -*- Python -*-
# $Id$

"""Wrapper functions for Linux /proc/meminfo
"""

import string

MEMINFO = "/proc/meminfo"
JUNK_LINES = 3

True = (1==1)
False = not True

def meminfo():
    f = open(MEMINFO)

    junk = JUNK_LINES
    d = {}
    for l in f.xreadlines():
        if junk:
            junk = junk - 1
            continue

        key,value,units = string.split(l)
        key = key[:-1]
        value = long(value)
        d[key] = value

    f.close()
    return d

def meminfo_string():
    m = meminfo()

    m['MemUtilization'] = (100.0 - 100.0 * m['MemFree'] / m['MemTotal'])
    m['SwapUtilization'] = (100.0 - 100.0 * m['SwapFree'] / m['SwapTotal'])

    l = \
"""\
Mem  %(MemUtilization)2.1f%% of %(MemTotal)-7d Cached:%(Cached)6d Active:%(Active)6d Buffers:%(Buffers)6d
Swap %(SwapUtilization)2.1f%% of %(SwapTotal)-7d Cached:%(SwapCached)6d
"""
    return l % m

if __name__ == '__main__':
    print meminfo_string()
