#!/bin/sh

set -e

DATABASE=data
DRIVES="$@"
STATUS=0

if [ -z "$DRIVES" ]; then
    echo "Error: No drive logicalnames specified (ex: $0 sda sdb sdc)"
    exit 2
fi

TMPFILE=$(mktemp)

lshw -class disk -xml | tr -d '[\n]' | sed -r 's,</node>\s+<node,</node>\n<node,g' > $TMPFILE
for DRIVE in $DRIVES; do
    FIND="<logicalname>/dev/${DRIVE}</logicalname>"
    if grep "$FIND" $TMPFILE | grep -q '<serial>'; then
        SERIAL=$(grep "$FIND" $TMPFILE | sed -r 's,^.*<serial>([^<]+)</serial>.*$,\1,')
#        echo "Debug: Checking drive $DRIVE with serial $SERIAL"
        if [ "$(wget -q -O - "http://${DATABASE}/disktest_runs/check_passed/${SERIAL}")" != "true" ]; then
            echo "Error: No PASSED disktest run found for $DRIVE with serial $SERIAL"
            STATUS=1
        fi
    else
	SERIAL="Unknown Serial"
        echo "Warning: Could not determine serial number for drive $DRIVE"
    fi
done

rm -f $TMPFILE
exit $STATUS
