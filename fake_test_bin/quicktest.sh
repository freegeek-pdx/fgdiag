#!/bin/sh

# used on a xen virtual machine to very easily test disktest (smartctl and lshw have problems normally)

EXTRA_OPTS=""
EXTRA_OPTS="DISKTEST_TIME_LIMIT_PER_GB=10"

set -e

TEST_BASE=$(dirname $(readlink -f $0))
TEST_LIB=$(readlink -f ${TEST_BASE}/../lib)
sudo env DISKTEST_NO_SYSLOG=true DISKTEST_DATA_SECURITY_BATCH_MODE=true PATH=$TEST_BASE:/sbin:$PATH RUBYLIB=$TEST_LIB DISKTEST_LOGTO_FGDB=localhost:3000 DISKTEST_REQUIRED_NUMBER_OF_DRIVES=1 DISKTEST_DISK_REGEX=xvd[bc] $EXTRA_OPTS ./bin/disktest
