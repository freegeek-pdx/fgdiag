#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11:/usr/games
export PATH

FREEKBOX_POSTCLONE_D=/etc/lessdisks-cloner/
export FREEKBOX_POSTCLONE_D

if [ ! -d $FREEKBOX_POSTCLONE_D ]
then
    echo WTF -- $FREEKBOX_POSTCLONE_D is missing?
    exit 1			# should be impossible
fi

cd ${FREEKBOX_POSTCLONE_D}

# Need "/proc" for /proc/mounts; make certain it's mounted:
#
mount -t proc proc /proc >/dev/null 2>&1
# mount -t devfs devfs /dev

# open a terminal for debugging purposes... we default to ash because it's light-weight..
#if [ -x /bin/ash ]; then
#  dbgshell="/bin/ash"
#else
#  dbgshell="/bin/bash"
#fi
#echo "Debug shell open on vt2; use Alt-F2 to get there."
#openvt $dbgshell

## ROOT_DEV=$(cat /proc/mounts | grep "${TARGET}" ....XXXX )

# Perform device detection first; must do sound first so that sb will
# always be loaded before probes for isa-pnp ethernet cards, in
# particular, the Etherlink III 3c509 and 3c509B.
#
#ifdown eth0 >/dev/null 2>&1
#ifconfig eth0 down >/dev/null 2>&1
#rmmod 3c509 >/dev/null 2>&1
#rmmod isa-pnp >/dev/null 2>&1

# Always configure soundcard first.
#
#echo "Running 'sndconfig'."
#sndconfig

echo "Removing potentially incorrect /dev/modem and /dev/mouse symlinks."
rm -f /dev/modem /dev/mouse

echo "Lets hope that kudzu fixes them for us; if not, do it by hand."

#echo "Running 'kudzu'."
# using the -q flag, for quiet mode, which will not prompt the user for changes
#kudzu -q

echo -n "Running 'update-modules' to rebuild /etc/modules.conf; please wait..."
update-modules
echo " Done."

# Make sure that "sb" loads first after reboot.
#
#if grep -q '^driver: sb' /etc/sysconfig/hwconf
#then
#    echo "Adding sb (soundblaster) and opl3 (synthesizer) to /etc/modules."
#    echo sb   >> /etc/modules
#    echo opl3 >> /etc/modules
#fi

#if grep -q '3c509' /etc/sysconfig/hwconf
#then
#    echo "Adding 3c509 (ethernet) driver to /etc/modules."
#    echo 3c509 >> /etc/modules
#fi

# if no ethernet card is available, attempt to configure one
#if [ -z "$(ifconfig eth0)" ]; then
#  ./etherprobe
#fi

# start networking during initial boot
if [ -n "$(ifconfig eth0)" ]; then
#  ifup eth0

  # Freegeek-ism....
  echo "Setting the clock..."
  ntpdate pool.ntp.org
  hwclock --systohc --utc
  echo "Done."
  echo "Timezone is: $(cat /etc/timezone)"
  echo "Local date is: $(date '+%Y/%m/%d %H:%M:%S (%Z)')"
  echo "UTC date is  : $(date --utc '+%Y/%m/%d %H:%M:%S (%Z)')"
else
  echo "manual configuration of network card is necessary..."
  sleep 10
fi

# Reconfigure the X Server
echo "About to configure the X Server..."

#swiftx --test && continue="yes"

magix

echo  "Done!"

alsaconf


#PATH="/usr/local/lib/easydialog:/usr/lib/easydialog:$PATH" . easydialog.sh

# set default width for easydialog so we can actually read it.
#WIDTH=75

#while [ "$continue" != "yes" ]; do
#  radioBox "X Configuration" "X configuration acceptable?" \
#    accept "keyboard, mouse, video all looked good" off \
#    retry "try again using swiftx, maybe change mouse settings" off \
#    swiftx-v3 "swiftx, X version 3 only" on \
#    freex "try again using freex" off \
#    oldretry "try again using old system" off \
#    skip "X configuration failed, give up and skip it..." off

#  case $REPLY in
#    accept) continue="yes" ;;
#    retry) swiftx --test && continue="yes" ;;
#    swiftx-v3) swiftx --test -x3 && continue="yes" ;;
#    freex) freex
#     xinit /etc/testscripts/xvidcheck ;;
#    oldretry) ./x-server ;;
#    skip) continue="yes" 
#      rm -v /etc/X11/X /etc/X11/XF86Config ;;
#  esac
#done

echo "Removing postclone init hook: /etc/rcS.d/$(basename $0)"
rm -f /etc/rcS.d/$(basename $0)
exit 0
