"""FreeGeek Database access."""

import MySQLdb

def connect(dburl):
    """Return a Database instance connected to dburl.

    Attempt to connect to dburl, and fail gracefully by falling back to a temporary file cache.

    """
    try:
        # (Insert connection code here)
        # db = something
        pass
    except:
        # (Insert graceful failure here) ;)
        pass

    return db


class Database:
    def __init__(self, conn):
        self.__conn = conn
        self.__field_map = FieldMap(self.__conn)

    def get_gizmo_by_id(gid):
        """Get a Gizmo and return an object."""

    def __get_conn():
        return self.__conn

    def __get_field_map():
        return self.__field_map

    connection = property(__get_conn, doc='Connection object for the Database')
    field_map = property(__get_field_map, doc='FieldMap of the Database')

class Gizmo:
    # FIXME:
    # For SQLObject implementation, take SQLObject instance in __init__
    # For MySQLdb, take MySQLdb connection.

    def register_test_data(data):
        """Put data into appropriate fields in database"""

class FieldMap:
    # Same as Gizmo

    def get_field_location(fieldname):
        """Return the Table fieldname belongs to."""
