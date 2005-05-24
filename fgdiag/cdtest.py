#!/usr/bin/env python

""" Testing cdrom drive 

    - Derived from perl script "testcd"  

"""

from lib import test, userinteraction
from lib.logging import create_node

import string 
import commands 
import os

# Create main log node
_log = create_node(__name__)

# ------  Constants (lifted from cdtest) --------

# How many MB to read during test
megstoread = 10;

# Size of each read block
BlockSize = 1024 * 1024;

# Number of blocks to read
BlockCount = (megstoread * 1024 * 1024) / BlockSize;

# First calculate optimal offset (in blocks) from start of data
# device to place at which reading begins
# (Divide number of bytes to skip by the block size)
###        NOTE:  $Skip may be adjusted down in test loop      ###

BytesToSkip = (5.9 * 100) * (1024 * 1024);
Skip = BytesToSkip / BlockSize;

# Calculate last byte to be read
LastByteToRead = (Skip * BlockSize) + (BlockCount * BlockSize);

# Some nominal values that can be used to educate testers about
# the usefulness of the CD disc they are using to test speed.
OptimalMbOnDisc = 600;
WarningMbOnDisc = 300;
# And to disallow testing with a disc that has too little data.
MinimumMbOnDisc = 200;

#
# End   CONSTANTS


# ---------  Functions  --------------

# Parse the output of the unix 'time' command, 
# returning results in seconds.

def parse_shell_elapsed_time(s_time_output):

  s_time_output  =  s_time_output.split()

  for i in range(len(s_time_output)):
    if (s_time_output[i] == 'real'):
      s_elapsed_time = s_time_output[i+1]

  minutes = string.atof(s_elapsed_time[0])
  seconds = string.atof(s_elapsed_time[2:-1])

  if minutes > 0:
    seconds = seconds + minutes * 60
  return(seconds)

# Parse the output of the Gnu 'time' command,
# returning results in seconds.

def parse_GNU_elapsed_time(s_time_output):

  s_time_output  =  s_time_output.split()

  for s_elapsed_time in s_time_output:
    if (string.find(s_elapsed_time,'elapsed') > 0): 
      break 

  seconds = string.atof(s_elapsed_time[2:-7])
  minutes = string.atof(s_elapsed_time[0])

  if minutes > 0:
    seconds = seconds + minutes * 60
    
  return(seconds)


def CD_scan():
    return (CDDevice(),)

class CDDevice(test.TestableDevice):

    # English name of the device tested
    name = "CD Drive"

    def __init__(self):
        # Create log node for this object
        self.__log = _log.child_node("CDDevice")
        # Run inherited __init__
        test.TestableDevice.__init__(self)

    def _d_test(self):

        if self.data["manufacturer"] == "No CD Drive Found": 
          userinteraction.error("No CD Drive found." )
          return test.Status["Failed"]

 	self.data["interface"] = "IDE" 

        # Grep dmesg for medium warning...

        status, output = commands.getstatusoutput('/bin/dmesg | grep "No medium"')
        if status==0:
          userinteraction.error("No medium found. You probably have a bad CD. \nInsert another CD and try again. \nIf this continues, the drive may be bad.")
          return test.Status["Failed"]

        # Try to determine the amount of data on the cdrom drive and 
        # adjust Skip if need be.

        MbOnDisc = 0 
        cmd = 'mount -tiso9660 /dev/' + self.device + ' /mnt 2>&1' 
        status, output = commands.getstatusoutput(cmd)
        if not status==0:
          userinteraction.error("\n--> Mount failed. \n    If this continues, the drive may be bad. \n    Insert another CD and try again.") 
        #  return test.Status["Failed"]
          working = userinteraction.yesno("    Continue?", " ") 
          if working==0:
            return test.Status["Failed"]
          else:
            return test.Status["Unknown"]

        cmd = 'cat /proc/ide/' + self.device + '/capacity' 
        status, output = commands.getstatusoutput(cmd)
        blocks = output

        cmd = 'umount /dev/' + self.device 
        status, output = commands.getstatusoutput(cmd)

        MbOnDisc = (int(blocks) / (1024 *2))

        notice_string = ''
        
#        if (MbOnDisc < MinimumMbOnDisc):
#          userinteraction.error("This CD disc has less than  " + str(MinimumMbOnDisc) + " MB of data.\nNo test will be performed.\n\n")
#          return test.Status["Failed"]

        if (MbOnDisc < WarningMbOnDisc):
          notice_string = ("This CD disc has less than  " + str(WarningMbOnDisc) + " MB of data. By testing it you will almost surely understate the true\nspeed of the CD drive that you are testing.\n")
        else:
          if (MbOnDisc < OptimalMbOnDisc):
            notice_string = ("  This CD disc that you are using to test has insufficient data for properly testing the CD drive's speed.\n  It is recommended that you use a disc with more than " + str(OptimalMbOnDisc) + " MB of data.\n")

	if ( (MbOnDisc * 1024 * 1024) < LastByteToRead ):
          # adjust skip value to allow read to fall within
          # limit of data on this CD disc
          global Skip
          Skip = ( (MbOnDisc - 1.5 * megstoread ) * 1024 * 1024) / BlockSize

        notice_string = notice_string + 'Testing '                     \
        +           self.device + ': ' + self.data["manufacturer"]     \
        + '\n        MB to Read    : ' + str(megstoread)               \
        + '\n        Block Size    : ' + str(BlockSize)                \
        + '\n        Blocks to Skip: ' + str(Skip)                     \
        + '\n        Blocks to Read: ' + str(BlockCount)               \
        + '\n        MB on CD disc : ' + str(MbOnDisc)

        userinteraction.notice(notice_string)

        cmd = '/usr/bin/time dd if=/dev/' + self.device \
        + ' of=/dev/null bs=' + str(BlockSize)          \
        + ' count=' + str(BlockCount)                   \
        + ' skip='  + str(int(Skip)) + ' 2>&1'

        # Get it spinning, then test. 
        status, output = commands.getstatusoutput(cmd)
        status, output = commands.getstatusoutput(cmd)
        status, output = commands.getstatusoutput(cmd)

        if (string.find(output,'real') > 0):
           elapsed_time = parse_shell_elapsed_time(output)
        else:
           elapsed_time = parse_GNU_elapsed_time(output)

        speed = round(((BlockSize * BlockCount) / elapsed_time) / (150 * 1024))
	formatted_speed = str(int(round(speed))) + 'x'
 	self.data["speed"] = formatted_speed 

        userinteraction.notice('Tested at ' + formatted_speed) 
        return test.Status["Passed"]

    def _d_data(self):

        # Look in /proc/ide/(device)/media for any cdrom info... 

        found=False
        for device in ('hda','hdb','hdc','hdd'):
          path = '/proc/ide/'+ device 
          if (os.path.exists(path + '/media')):
            f = open(path + '/media',"r")
            media = f.read(5)
            f.close()

            if media == 'cdrom':

              found=True
              self.device = device 

              f = open(path + '/model',"r")
              self.data["manufacturer"] = string.strip(f.read())
              f.close()

              f = open(path + '/capacity',"r")
              self.capacity = ( int(f.read()) / (1024 *2))
              f.close()

        if found == False:
          userinteraction.error("No CD Drive found.")
          self.data["manufacturer"] = "No CD Drive Found" 

	return self.data
         

    def _d_description(self, data):

        # Define code to make a description for a cd drive... 
 	return self.data["manufacturer"] 

class CDTester(test.GizmoTester):

    gizmotype = "Gizmo.Component.Drive.CDDrive"

    def scan(self):
        CDs = CD_scan()
        for CD in CDs:
            CD.get_data()
        return CDs

    # Keep testing until a 'Passed' or 'Failed' is returned...
    def run(self, CDs):
        for CD in CDs:
          check='Unknown'
          while (repr(CD.status) <> 'Failed'  
             and repr(CD.status) <> 'Passed'):
            CD.test()
        return CDs

    def destination(self, CD):
      if CD.status == test.Status["Passed"]:
         return test.Destination["Stored"], "Please put this CD drive in the \"Good CD Drive\" bin."
      else:
         return test.Destination["Recycled"], "Please put this CD drive in the Recycling bin."

def main():
    from lib import testscript
    testscript.start(CDTester)

if __name__ == '__main__': main()
