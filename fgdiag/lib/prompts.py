import userinteraction

def prompt_for_gizmo(db, wantedtype):
    """Ask for the ID of a Gizmo and get it."""
    goodgizmo = False
    gizmo = None
    
    while not goodgizmo:
        gid = userinteraction.prompt("Gizmo ID? ")
        gizmo = db.get_gizmo_by_id(gid)
        goodgizmo = True
        
        # Type Check
        gizmotype =  gizmo.get("classTree")
        if gizmotype!=wantedtype:
            goodgizmo = False
            userinteraction.warning("The type of the Gizmo you entered is %s, but a %s was expected. Please check and re-enter your Gizmo id." % (gizmotype, wantedtype))
            
        # Check for conflicting data?
        # Check if already tested (set testData field too?)
              
    return gizmo