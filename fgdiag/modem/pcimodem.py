#!/usr/bin/env python
# $Id$

"""Looks for modem devices in lspci.

Looks for telltale signs of a winmodem too.
"""

# Depends: pciutils

LSPCI = "/sbin/lspci"

import os, re
# sibling import
from pyutil import bold, exists_in_path

# Don't let the import succeed if we can't get lspci.
_lspci_fullpath = exists_in_path(LSPCI)
if not _lspci_fullpath:
    raise ImportError, "Couldn't find lspci at '%s'." % (LSPCI,)
else:
    if not os.access(_lspci_fullpath, os.X_OK):
        raise ImportError, "Couldn't run lspci at '%s'." % (_lspci_fullpath)
del _lspci_fullpath
del exists_in_path

serial_re = re.compile("(serial|communication) controller", re.IGNORECASE)
winmodem_re = re.compile("(win ?modem)|(HCF)", re.IGNORECASE)

def getModems():
    """Return a list of strings identifying PCI devices which might be modems.
    """

    lspci = os.popen(LSPCI, 'r')
    output = lspci.readlines()

    lspci_error = lspci.close()
    if lspci_error:
        raise RuntimeError, ("%s returned with exit code %s" %
                             (LSPCI, lspci_error))

    results = []

    for l in output:
        if serial_re.search(l):
            results.append(l)

    return results

def main():
    modems = getModems()

    if not modems:
        return

    print "%d PCI serial card%s found:" % (len(modems),
                                        ((len(modems) != 1) and 's') or '')

    for m in modems:
        winmodem = winmodem_re.search(m)
        if winmodem:
            print "%s - %s" % (m,bold("Winmodem!"))
        else:
            print m


if __name__ == "__main__":
    main()
