"""FreeGeek Database access."""

import MySQLdb

def connect(host, db, user, passwd):
    """Return a Database instance connected to dburl.
        
    Attempt to connect to dburl, and fail gracefully by falling back to a temporary file cache.
        
    """
    try:
        conn = MySQLdb.connect(host=host, db=db, user=user, passwd=passwd)
        mydb = Database(conn)
    except:
        # (Insert graceful failure here) ;)
        raise
    
    return mydb
    
class Database:
    def __init__(self, conn):
        self.__conn = conn
        self.__field_map = FieldMap(self.__conn)

    def get_gizmo_by_id(self, gid):
        """Get a Gizmo and return an object."""
    
    def __get_conn():
        return self.__conn
            
    def __get_field_map():
        return self.__field_map
    
    connection = property(__get_conn, doc='Connection object for the Database.')
    field_map = property(__get_field_map, doc='FieldMap of the Database.')

class Gizmo:	
    def __init__(self, conn):
        self.__conn = conn
            
    def register_test_data(self, data):
        """Put data into appropriate fields in database."""

class FieldMap:
    def __init__(self, conn):
        self.__conn = conn
    
    def get_field_location(self, fieldname):
        """Return the Table fieldname belongs to."""