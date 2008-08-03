#!/usr/bin/ruby

require './bin/disktest'

sleep 5

clear_stdin

print "Type something: "
puts "Saw: " + $stdin.gets
