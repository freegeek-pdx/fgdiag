import userinteraction
from fgdb import InvalidRowError

def prompt_for_gizmo(db, wantedtype):
    """Ask for the ID of a Gizmo and get it."""
    goodgizmo = False
    gizmo = None
    
    while not goodgizmo:
        gid = userinteraction.prompt("Gizmo ID? ")
        
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
        
        # Check if already tested?
        #if gizmo.get("testData"):
        #    answer = userinteraction.yesno("The Gizmo you entered has already been tested. Do you want to test it anyway?")
        #    if not answer:
        #        goodgizmo = False            
        #    
        # Check for conflicting data?
        
        # If it gets this far it's an ok gizmo
        goodgizmo = True
              
    return gizmo