"""FreeGeek Database access.

Example:
    
>>> db = fgdb.connect('localhost','fgdbtest','fgdbtester','freegeek')
>>> cd = db.get_table("CDDrive")
>>> row = cd.get_row(72558)
>>> row.get_column(("scsi",))
('N',)
>>> gizmo = db.get_gizmo_by_id(72558)
>>> db.field_map.get_field_location(gizmo.class_tree.split('.'), "working")
'Gizmo'
>>> db.field_map.get_field_location(gizmo.class_tree.split('.'), "notes")
'Gizmo'
>>> gizmo.set_column({"notes":"FreeGeek Database Python Access Is Working"})
True
>>> gizmo.get_column(("notes",))
('FreeGeek Database Python Access Is Working',)
>>> gizmo.table
<fgdb.Table instance at 0x4020306c>
"""

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

class Factory:
    """
    Generic class factory
    
    Creates of instances of a class and keeps them for further use in a 
    list. If an instance with the same initial arguments already exists,
    it will return the existing instance. Supports in-place substitution
    with an existing class.
    """
    # Should this go in pyutil?
    # I was going to use this for Tables but decided against it, may be useful later.
    # Question: Which if any of the below classes would benefit from this?
    # None currently have any stored state, but that may change in the future.
        
    def __init__(self, cls):
        self.__cls = cls
        self.__existing = dict()
        
    def __call__(self, *args, **kwds):
        return self.get(*args, **kwds)
    
    def get(self, *args, **kwds):
        totalargs = args + tuple(kwds.keys()) + tuple(kwds.values())
        if not self.__existing.has_key(totalargs):
            self.__existing[totalargs] = self.__cls(*args, **kwds)
        return self.__existing[totalargs] 
    
class Database:
    def __init__(self, conn):
        self.__conn = conn
        self.__field_map = FieldMap(self)
        
    def get_table(self, name, idname = "id"):
        """Get Table object by name."""
        return Table(self, name, idname)
        
    def get_gizmo_by_id(self, gid):
        """Get a Gizmo and return an object."""
        return Gizmo(self, gid)
    
    def query_one(self, sql):
        c = self.__conn.cursor()
        c.execute(sql)
        return c.fetchone()
    
    def execute(self, sql):
        c = self.__conn.cursor()
        c.execute(sql)
        return True
        
    def __get_conn(self):
        return self.__conn
            
    def __get_field_map(self):
        return self.__field_map
    
    connection = property(__get_conn, doc="Connection object for the Database.")
    field_map = property(__get_field_map, doc="FieldMap of the Database.")

class Table:
    def __init__(self, db, name, idname = "id"):
        self.__db = db
        self.__name = name
        self.__idname = idname
    
    def get_row(self, id_):
        return TableRow(self, id_, self.__idname)
        
    def get_column_by_id(self, id_, fields):
        sql = "SELECT %s FROM %s WHERE %s = %s" % (", ".join(fields), self.__name, self.__idname, id_)
        return self.__db.query_one(sql)
    
    def set_column_by_id(self, id_, fields):
        sets = tuple()
        for item in fields.iteritems():
            sets = sets + ("%s = '%s'" % (item[0], item[1]),)
        sql = "UPDATE %s SET %s WHERE %s = %s" % (self.__name, ', '.join(sets), self.__idname, id_)
        return self.__db.execute(sql)
        
    def __get_name(self):
        return self.__name
    
    def __get_database(self):
        return self.__db    
    
    name = property(__get_name, doc="Name of Table in the Database.")
    database = property(__get_database, doc="Database this Table.")

class TableRow:
    def __init__(self, tb, id_, idname = "id"):
        self.__tb = tb
        self.__id = id_
    
    def get_column(self, fields):
        return self.__tb.get_column_by_id(self.__id, fields)
    
    def set_column(self, fields):
        return self.__tb.set_column_by_id(self.__id, fields)
    
    def __get_table(self):
        return self.__tb
    
    table = property(__get_table, doc="Name of Table containing this TableRow.")
    
class Gizmo(TableRow):	
    def __init__(self, db, gid):
        # This is where I was planning to use Factory; is it bad to be passing each Gizmo a different Table? I think it is (bad)...
        TableRow.__init__(self, db.get_table("Gizmo"), gid)   
        
    def __get_class_tree(self):
        return self.get_column(("classTree",))[0]
    
    class_tree = property(__get_class_tree, doc="Class Tree of the Gizmo.")

class FieldMap(Table):
    def __init__(self, db):
        Table.__init__(self, db, "FieldMap")
        
    def get_field_location(self, classes, fieldname):
        """Return the Table fieldname belongs to."""
        sql = "SELECT tableName FROM fieldMap WHERE tableName IN %s AND fieldName='%s'" % (repr(tuple(classes)), fieldname)
        # Table because according to the private var naming __db belongs to table...
        # Fix by making __db not private or keeping separate __dbs?
        tablename = self.database.query_one(sql)[0]
        return tablename