#!/usr/bin/env python2.2

""" Testing cdrom drive 

    - determines mount point
    - mounts cd
    - tests speed

"""

# from lib import test, userinteraction
# from lib.logging import create_node

import string 
import commands 
import test, userinteraction
from logging import create_node

# Create main log node
_log = create_node(__name__)


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

def parse_GNU_elapsed_time(s_time_output):

  s_time_output  =  s_time_output.split()

  for s_elapsed_time in s_time_output:
    if (string.find(s_elapsed_time,'elapsed') > 0): 
      break 

  minutes = string.atof(s_elapsed_time[0])
  s_elapsed_time =  s_time_output[8]

  seconds = string.atof(s_elapsed_time[2:-7])
  minutes = string.atof(s_elapsed_time[0])

  if minutes > 0:
    seconds = seconds + minutes * 60
    
  return(seconds)


# ------  Constants (derived from cdpseed.sh) --------

#  TransferAmount =  how many bytes to transfer each pass

TransferAmount = 20 * 1024 * 1024

#  ByteSkipIndex VALUE indicates to index into the device an
#  additional VALUE bytes prior to starting each cycle of testing

ByteSkipIndex = 1024 * 1024

# MaxMul is a short cut for trying out vastly different blocksizes

MaxMul = 1000

#  CountConstant is used to calculate number of blocks to transfer
#  during each cycle
#  see: $MaxMul

CountConstant=TransferAmount / MaxMul

#  DefaultSkipFactorCount sets the default number of different
#  SkipFactor values to utilize when calculating Skip value

DefaultSkipFactorCount=4

#  DefaultPassCount sets the default number of read trials to run
#  for each unique set of options passed to 'dd'

DefaultPassCount=1

#  Blocksize

Blocksize = 1024

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

    def run_command(self, command):
        self.__log("Run", "Running \"%s\"." % command)
        status, output = commands.getstatusoutput(command)
        self.__log("Run", "Returned Status: %s." % status)
        self.__log("Run", "Returned Output: \"%s\"." % output)
        return status, output

    def _d_test(self):
        userinteraction.prompt("Insert CD", "Please put a data CD in the drive 'to be tested' and press enter.")

        # Get mount point. 
        # Try grepping dmesg first... 

        userinteraction.notice("Looking for mount point...")
        status, output = self.run_command("dmesg | grep ^hd | grep CD | awk '{print $1}' | sort -u")
        device=string.join(["/dev/",output],"")
        cmd=string.join(["mount ",device])
        status, output = self.run_command(cmd)

        # If that doesn't work, try fstab...  

        if not status==0:
            status, output = self.run_command("cat /etc/fstab | grep cd | awk '{print $1}' | sort -u")
            device=output
            cmd=string.join(["mount",device])
            status, output = self.run_command(cmd)

        # If that doesn't work, bail.  

        if not status==0:
           userinteraction.error("Can't find mount point")
           return test.Status["Failed"]


        # Test drive speed.... 

        userinteraction.notice("Testing drive speed....")

        mul        = MaxMul
        Count      = CountConstant / mul
        blocksize  = 1024
        Blocksize  = blocksize * mul
        SkipFactor = 1
        Skip       = 0

        cmd=string.join(["time dd if=",device, " of=/dev/null bs=",str(Blocksize), " count=", str(Count), " skip=", str(Skip)],"")
    
        status, output = self.run_command(cmd)
        if not status==0:
           userinteraction.error("Can't read from CD...")
           cmd=string.join(["umount",device])
           status, output = self.run_command(cmd)
           return test.Status["Failed"]

        if (string.find(output,'real') > 0):
           elapsed_time = parse_shell_elapsed_time(output)
        else:
           elapsed_time = parse_GNU_elapsed_time(output)

        # Determine speed.... 
        # Single speed is 150kbs/sec. 
        # speed = (bytes read / seconds ) / (150 * 1024)

        speed= round(((Blocksize * Count) / elapsed_time) / (150 * 1024)) 
        msg = string.join(['speed: ',str(speed),'x'])  
        userinteraction.notice(msg)

        cmd=string.join(["umount",device])
        status, output = self.run_command(cmd)
	return test.Status["Passed"]

    def _d_data(self):
        # Define code to get data on the cd drive here...
        return {}

    def data(self):
        # Define code to get data on the cd drive here...
        return {}


    def _d_description(self, data):
        # Define code to make a description for a cd drive... 
        return None 

class CDTester(test.GizmoTester):

    gizmotype = "Gizmo.Component.CDDrive"

    def run(self):
        # Define test logic for a Pogo Stick here. Usually this is pretty
        # straightforward, like in this case.
        CDs = CD_scan()
        for CD in CDs:
            CD.get_data()
            CD.test()
        return CDs

'''
    def destination(self, pogo):
        if pogo.data["notes"] == "Colored Purple":
            return test.Destination["Stored"], "Purple Pogo"
        else:
            return test.Destination["Recycled"], "Recycling"
'''

def main():
#    from lib import testscript
    import testscript
    testscript.start(CDTester)

if __name__ == '__main__': main()

