require 'soap/rpc/driver'
require 'rubytui'

class DisktestLogException < StandardError
end

class DisktestLog
  def self.server
    ENV["DISKTEST_LOGTO_FGDB"]
  end

  def self.enabled?
    ! (DisktestLog.server.nil? or DisktestLog.server.empty?)
  end

  def self.prepare
    return if defined?(@@driver) or ! DisktestLog.enabled?
    @@driver = SOAP::RPC::Driver.new("http://#{server}/", "urn:disktest")
    @@driver.add_method("ping")
    @@driver.add_method("soap_methods")
    begin
      retval = @@driver.ping
      if retval != "pong"
        raise DisktestLogException.new("I could not connect to the server.\nMake sure you are connected to the network and try again.\n\n")
      end
    rescue SOAP::FaultError => e
      raise DisktestLogException.new("Server returned this error: #{e.message}\n\n")
    rescue DisktestLogException => e
      raise e
    rescue SOAP::RPCRoutingError, SOAP::ResponseFormatError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETDOWN, Errno::ENETUNREACH, Errno::ECONNRESET, Errno::ETIMEDOUT, NoMethodError, SocketError, NameError => e
      raise DisktestLogException.new("I could not connect to the server (#{e.message}).\nMake sure you are connected to the network and try again.\n\n")
    end
    @@soap_methods = @@driver.soap_methods
    @@soap_methods.each{|x|
      @@driver.add_method(*x)
    }
  end

  def self.already_testing?(vendor, model, serial_number)
    self.prepare
    return false if !DisktestLog.enabled?
    return @@driver.check_disktest_running(vendor, model, serial_number)
  end

  attr_reader :this_id #, :vendor, :model, :serial_number, :result

  def initialize(vendor, model, serial_number, size, bus_type)
#    @vendor = vendor
#    @model = model
#    @serial_number = serial_number
    return if !DisktestLog.enabled?
    begin
      self.class.prepare
      @this_id = @@driver.new_disktest_run(vendor, model, serial_number, size, bus_type)
    rescue SOAP::FaultError => e
      raise DisktestLogException.new("Server returned this error: #{e.message}\n\n")
    end
  end

  def update_serial(serial)
    return if !DisktestLog.enabled?
    begin
      @@driver.update_serial(@this_id, serial)
    rescue SOAP::RPCRoutingError, SOAP::ResponseFormatError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETDOWN, Errno::ENETUNREACH, Errno::ECONNRESET, Errno::ETIMEDOUT, NoMethodError, SocketError, NameError, SOAP::FaultError => e
      raise DisktestLogException.new(e.message)
    end
  end

  def started(start_time)
    return if !DisktestLog.enabled?
    begin
      @@driver.add_disktest_started(@this_id, start_time.to_s)
    rescue SOAP::RPCRoutingError, SOAP::ResponseFormatError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETDOWN, Errno::ENETUNREACH, Errno::ECONNRESET, Errno::ETIMEDOUT, NoMethodError, SocketError, NameError, SOAP::FaultError => e
      raise DisktestLogException.new(e.message)
    end
  end

  def complete(result, complete_time, details, log)
#    @result = result
    return if !DisktestLog.enabled?
    begin
      @@driver.add_disktest_completed_log(@this_id, result, complete_time.to_s, details, log)
    rescue SOAP::RPCRoutingError, SOAP::ResponseFormatError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETDOWN, Errno::ENETUNREACH, Errno::ECONNRESET, Errno::ETIMEDOUT, NoMethodError, SocketError, NameError, SOAP::FaultError => e
      raise DisktestLogException.new(e.message)
    end
# FOR DEBUG:    raise DisktestLogException.new("THIS IS A TEST") if File.exists?('/tmp/err')
  end
end
