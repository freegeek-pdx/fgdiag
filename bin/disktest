#!/usr/bin/ruby

require 'rubytui'
include RubyTUI

class HardDrive
  MODULES = %w[ide_core ide_disk ide_generic]
  PASSED = 0
  FAILED = 1
  UNTESTED = 2

  def HardDrive.scan
    # load the modules
    # look for possible drives
    # return an instance for each
    return [HardDrive.new('/dev/hda')]
  end

  def initialize(dev)
    @dev = dev
    @testing = false
    @status = UNTESTED
  end
  attr_reader :dev, :testing

  def run_tests
    return if @testing
    @testing = true
    @thread = Thread.new {
      smart &&
      badblocks &&
      smart &&
      wipe &&
      smart
      @testing = false
    }
    return @thread
  end

  def smart
  end

  def badblocks
  end

  def wipe
  end

  def output_display
    message(dev + ": ")
    highlight(status)
    puts
  end

  def status
    case @status
    when PASSED
      'all tests passed'
    when FAILED
      'failed'
    when UNTESTED
      'untested'
    end
  end
end

if __FILE__ == $0
  require 'optparse'
  trap( "SIGINT" ) do
    #`reset -Q`
    errorMessage "\n\nUser interrupt caught.  Exiting.\n\n"
    exit!( 1 )
  end
  # check that i'm root
  # alter the syslogs
  drives = HardDrive.scan
  threads = drives.map {|drive| drive.run_tests}
  until threads.empty?
    `clear`
    drives.each {|d| d.output_display}
    threads = threads.find_all {|t|
      t.alive? 
    }
    sleep 10
  end
  # test them, displaying progress
  # report
end
