# -*- Python -*-
# $Id$

"""Misc. general-purpose utility functions."""

import os, string, sys
from os import path
import fcntl

PAGER = None

def exists_in_path(filename, search_path=None):
    """Does the file exist in the given search path?

    If so, return the absolute path.  If not, return False.
    search_path defaults to $PATH.
    """
    if path.isabs(filename):
        return (path.isfile(filename) and filename)

    if search_path is None:
        search_path = os.environ["PATH"]

    directories = string.split(search_path, ":")

    for d in directories:
        found = path.isfile(path.join(d, filename))
        if found:
            return path.join(d, filename)

    return None

def bold(s):
    """Surround a string with bold/unbold ANSI codes.
    """
    return "\033[1m%s\033[0m" % (s, )

def makeNonBlocking(fd):
    # from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52296/
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NDELAY)

def withPager(callable, *args, **keywords):
    global PAGER
    if PAGER is None:
        PAGER=os.environ.get("PAGER",
                             "less --quit-if-one-screen --RAW-CONTROL-CHARS --silent --LONG-PROMPT")

    oldout = sys.stdout
    sys.stdout = os.popen(PAGER, "w", 0)
    try:
        retval = callable(*args, **keywords)
    finally:
        sys.stdout = oldout

    return retval
