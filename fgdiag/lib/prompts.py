import userinteraction
from fgdb import InvalidRowError

def prompt_for_gizmo(db, wantedtype):
    """Ask for the ID of a Gizmo and get it."""
    goodgizmo = False
    gizmo = None
    
    while not goodgizmo:
        gid = userinteraction.prompt("Gizmo ID?", "What is the id for the Gizmo being tested?")
        
        # Existence Check
        try:
            gizmo = db.get_gizmo_by_id(gid)
        except InvalidRowError:
            userinteraction.warning("The Gizmo you entered does not exist. Please check and re-enter your Gizmo id.")
            continue
            
        # Type Check
        gizmotype = gizmo.get("classTree")
        if gizmotype!=wantedtype:
            userinteraction.warning("The type of the Gizmo you entered is %s, but a %s was expected. Please check and re-enter your Gizmo id." % (gizmotype, wantedtype))
            continue
        
        # If it gets this far it's an ok gizmo
        goodgizmo = True
              
    return gizmo

def confirm_data(data, id_):
    datalist = tuple()
    for field, value in data.iteritems():
        datalist += ("  %s: %s" % (field, value),)
    datastring = "\n".join(datalist)
    body = """The following data will be sent to the FreeGeek Database:
---
Gizmo %s:
%s
---
Is this information correct?""" % (id_, datastring)
    return userinteraction.yesno("Confirmation", body)
    
def db_fallback_notice(filename):
    """Alert about fallback if database fails."""
    userinteraction.notice("Unable to establish a connection with the FreeGeek Database. Outputting test results to a file named %s. " % (filename))
