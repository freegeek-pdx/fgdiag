import os
from ConfigParser import ConfigParser, NoOptionError

def get_config():
    """Return a ConfigParser for FreeGeek config."""
    config = ConfigParser()
    config.add_section("fgdb")

    locations = list()
    locations.append("/etc/freegeekrc")
    locations.append("/etc/fgrc")
    locations.append(os.path.join(os.getenv("HOME"),".freegeekrc"))
    locations.append(os.path.join(os.getenv("HOME"),".fgrc"))
    locations.append(os.path.join(os.curdir,"freegeekrc"))
    locations.append(os.path.join(os.curdir,"fgrc"))
    
    config.read(locations)
    
    return config

def get_fgdb_login():
    #Error trapping needed?
    config = get_config()
    host = config.get("fgdb","host")
    db = config.get("fgdb","db")
    user = config.get("fgdb","user")
    passwd = config.get("fgdb","passwd")
    
    return host, db, user, passwd
    
