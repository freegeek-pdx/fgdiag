#!/usr/bin/env python
# $Id$

"""Summarize ISA PnP devices as reported by isapnptools\'s pnpdump."""

# pnpdump (in isapnptools)
# Catch from '^# Card \d: '
# to '^#$'

import os, re, string

PNPDUMP="/usr/sbin/pnpdump"

info_start = re.compile("^# Card \d+:")
info_end = re.compile("^#$")

ansi_string = re.compile("^#.*?ANSI string --\>(.*?)\<--")

def getCards():
    pnpdump = os.popen(PNPDUMP, 'r')
    output = pnpdump.readlines()

    pnpdump_error = pnpdump.close()
    if pnpdump_error:
        raise RuntimeError, ("%s returned with exit code %s" %
                             (PNPDUMP, pnpdump_error))

    # 'cards' is a multi-line description with vendor Id and the like,
    # 'strings' is just the ANSI indentifier.
    cards = []
    strings = []

    this_card = None
    for l in output:
        a = ansi_string.search(l)
        if a:
            strings.append(a.group(1))

        if info_start.search(l):
            this_card = [l]
        elif (this_card is not None) and info_end.search(l):
            cards.append(string.join(this_card, ''))
            this_card = None
        elif this_card is not None:
            this_card.append(l)

    return strings # cards

def main():
    cards = getCards()
    if cards:
        print "%d ISA PnP card%s found:" % (len(cards),
                                            ((len(cards) != 1) and 's') or '')
    for card in cards:
        print card

if __name__ == "__main__":
    main()
