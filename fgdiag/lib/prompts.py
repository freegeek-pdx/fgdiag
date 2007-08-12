import userinteraction
from errors import InvalidRowError, SQLError

def prompt_for_gizmos(db, wantedtype, devices):
    devicegizmos = dict()
    for device in devices:
        #print "%s (%s)" % (device.name, device.description)
        gizmo = prompt_for_id(db, wantedtype, device.name, device.description)

        devicegizmos[device] = gizmo
    return devicegizmos

def prompt_for_id(db, wantedtype, name, description=""):
    """Ask for the ID of a Gizmo and get it."""
    goodgizmo = False
    gizmo = None
    
    while not goodgizmo:
        gid = userinteraction.prompt("Gizmo ID?", "What is the id for the %s (%s) being tested? (blank if none)"%(name, description))
        if (gid == ""):
            goodgizmo = True
            continue
        
        # Existence Check
        try:
            gizmo = db.get_gizmo_by_id(gid)
        except ValueError:
            userinteraction.warning("The ID you entered does not seem to be valid, or may be too long. Please make sure it's a number and re-enter it.")
            continue
        except InvalidRowError:
            userinteraction.warning("The Gizmo you entered does not exist. Please check and re-enter your Gizmo id.")
            continue
        except SQLError:
            userinteraction.warning("The Database had a problem when the Gizmo you entered was requested. Please check and re-enter your Gizmo id.")
            continue
            
        # Type Check
        gizmotype = gizmo.get("classTree")
        if gizmotype!=wantedtype:
            userinteraction.warning("The type of the Gizmo you entered is %s, but a %s was expected. Please check and re-enter your Gizmo id." % (gizmotype, wantedtype))
            continue
        
        # If it gets this far it's an ok gizmo
        goodgizmo = True
              
    return gizmo

def prompt_for_classtree(classtree):
    abbrclasstree = dict()
    for gizmoclass in classtree:
        abbrclasstree[gizmoclass[gizmoclass.rfind("."):]] = gizmoclass
    body = """Avaliable Gizmo Classes:
---
%s
---
What class is this Gizmo?"""
    choice = userinteraction.prompt(body % "\n".join(abbrclasstree.keys()))
    return abbrclasstree[choice]
    
def confirm_data(devices, gizmos):
    datastringlist = list()
    template = """%s %s:
    %s"""
    for device in devices:
        gizmo = gizmos[device]
        if gizmo is None:
            idstring = "Will generate a Gizmo ID."
        else:
            idstring = "Gizmo ID: %s." % gizmo.id
        datastringlist.append(template%(device.name, device.description, idstring))
       
    body = """Data about the following Gizmos will be sent to the FreeGeek Database:
---
%s
---
Please double-check any Gizmo IDs you have entered before continuing.
Is this correct?""" % ("\n".join(datastringlist))
    return userinteraction.yesno("Confirmation", body)

def confirm_devices(devices):
    datastringlist = list()
    template = "%s: %s"
    for device in devices:
        datastringlist.append(template%(device.name, device.description))
    body = """Found these devices:
---
%s
---
Does this look right?""" % ("\n".join(datastringlist))
    return userinteraction.yesno("Confirmation", body)

def report_success(data):
    datastringlist = list()
    template = """%s %s:
    %s"""
    for name, description, instructions in data:
        datastringlist.append(template%(name, description, instructions))
    body = """Report:
---
%s
---
This test run is now finished. Press enter to reboot!""" % ("\n".join(datastringlist))
    userinteraction.prompt("Finished", body)

def db_fallback_notice(filename):
    """Alert about fallback if database fails."""
    userinteraction.notice("Unable to establish a connection with the FreeGeek Database. Outputting test results to a file named %s. " % (filename))
