import sys

filename = sys.argv[1].replace(".py","")
scanname=sys.argv[2]

try:
    m = __import__(filename)
except:
    print "Unable to import %s."%filename
    raise

print "Attempting to run scan function %s..."%scanname

try:
    scan = getattr(m, scanname)
except:
    print "Unable to load scan function %s"%scanname
    raise

try:
    scanresults = scan()
except:
    print "Scan failed, error:"
    raise

print "Scan Succeeded!"
print "Inspecting scan results..."

try:
    for device in scanresults:
        print "Device object %s, for testing %ss"%(device, device.name)
except AttributeError:
    print "Device has no \"name\" attribute! Please add an attribute called name with the descriptive name of what %s tests."%devicename
    raise

print "Attempting to run device functions..."
print "---"

for device in scanresults:
    print "Running get_data..."

    try:
	device.get_data()
    except:
	print "get_data failed."
	raise

    print "get_data Succeeded!"
    print "Description:"
    print device.description
    print "Data:"
    print device.data

    print "Running test..."
    try:
	device.test()
    except:
	print "test failed."
	raise

    print "test Succeeded!"
    print "Status:"
    print device.status

print "Everything seems to be functional."
