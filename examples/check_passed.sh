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

# TODO: lshw needs a udeb, which also might require one for libunwind7?
sudo lshw -class disk -xml | tr -d '[\n]' | sed -r 's,</node>\s+<node,</node>\n<node,g' > $TMPFILE
# TODO: remove sudo under d-i
for DRIVE in $DRIVES; do
    FIND="<logicalname>/dev/${DRIVE}</logicalname>"
    if grep "$FIND" $TMPFILE | grep -q '<serial>'; then
        SERIAL=$(grep "$FIND" $TMPFILE | sed -r 's,^.*<serial>([^<]+)</serial>.*$,\1,')
        # TODO: curl will need to be replaced
        echo "Debug: Checking drive $DRIVE with serial $SERIAL"
        if [ "$(curl -s "http://${DATABASE}/disktest_runs/check_passed/${SERIAL}")" != "true" ]; then
            echo "Error: No PASSED disktest run found with serial $SERIAL"
            STATUS=1
        fi
    else
        echo "Warning: for drive Unknown Serial"
    fi
done

rm -f $TMPFILE
exit $STATUS
