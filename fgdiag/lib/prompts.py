import userinteraction
from errors import InvalidRowError, SQLError

def prompt_for_ids(db, wantedtype, devices):
    devicegizmos = dict()
    for device in devices:
        devicegizmos[device] = prompt_for_id(db, wantedtype, device.name, device.description)
    return devicegizmos

def prompt_for_id(db, wantedtype, name, description=""):
    """Ask for the ID of a Gizmo and get it."""
    goodgizmo = False
    gizmo = None
    
    while not goodgizmo:
        gid = userinteraction.prompt("Gizmo ID?", "What is the id for the %s (%s) being tested?"%(name, description))
        
        # Existence Check
        try:
            gizmo = db.get_gizmo_by_id(gid)
        except ValueError:
            userinteraction.warning("The ID you entered does not seem to be a number. Please check and re-enter your Gizmo id.")
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

def confirm_data(iddata):
    alldatastring = ""
    for id_, data in iddata.iteritems():
        datalist = tuple()
        for field, value in data.iteritems():
            datalist += ("  %s: %s" % (field, value),)
        datastring = "\n".join(datalist)
        template = """Gizmo %s:
%s"""
        alldatastring = "\n".join((alldatastring,template%(id_, datastring)))

    body = """The following data will be sent to the FreeGeek Database:
---
%s
---
Is this information correct?""" % (alldatastring)
    return userinteraction.yesno("Confirmation", body)
    
def db_fallback_notice(filename):
    """Alert about fallback if database fails."""
    userinteraction.notice("Unable to establish a connection with the FreeGeek Database. Outputting test results to a file named %s. " % (filename))
