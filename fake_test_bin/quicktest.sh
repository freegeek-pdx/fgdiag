#!/bin/sh

# used on a xen virtual machine to very easily test disktest (smartctl and lshw have problems normally)

set -e

sudo env PATH=./fake_lshw_bin_for_tests:/sbin:$PATH RUBYLIB=lib DISKTEST_REQUIRED_NUMBER_OF_DRIVES=1 DISKTEST_DISK_REGEX=xvdb ./bin/disktest
