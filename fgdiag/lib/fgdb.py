
"""FreeGeek Database access.

Example:

>>> db = fgdb.connect("host","database","user","passwd")
>>> gizmo = db.get_gizmo_by_id(72558)
>>> gizmo.class_tree
'Gizmo.Component.Drive.CDDrive'
>>> gizmo.get("id","notes","value","speed","interface","inSysId")
(72558L, '', 0.0, '', '', 0L)
>>> gizmo.set(notes="FreeGeek Database Python Access Is Working")
True
>>> g.get("notes")
'FreeGeek Database Python Access Is Working'
>>> gizmo.table
<fgdb.FieldMapMultipleTable instance at 0x402b2c2c>

"""

from pyPgSQL import PgSQL

def connect(host, db, user, passwd):
    """Return a Database instance connected to dburl.

    Attempt to connect to dburl, and fail gracefully by falling back to a temporary file cache.

    """

    try:
        conn = PgSQL.connect(host=host, database=db, user=user, password=passwd)
        mydb = Database(conn)
    except:
        # (Insert graceful failure here) ;)
        raise

    return mydb

def _equals(field, value):
    return "%s = %s" % (field, PgSQL.PgQuoteString(str(value)))

def _AND(*l):
    return " AND ".join(l)

def _IN(*l):
    return " IN ".join(l)

def _single_tuple_list(l):
    l = tuple(l)
    newl = tuple()
    for item in l:
        newl += (item[0],)
    return newl

def _string_list(l):
    if len(l)==1:
        lstr = "(\"%s\")" % l[0]
    else:
        lstr = repr(tuple(l))
    return lstr

def _simplify_list(l):
    try:
        if len(l)==1:
    	     return l[0]
    	else:
                return l
    except:
        return l

def _tables(l):
    return ", ".join(l)

def _fields(l):
    return ", ".join(l)

def _values(valuedict):
    sets = tuple()
    for item in valuedict.iteritems():
        sets += (_equals(item[0],item[1]),)
    return _fields(sets)
    
def _id_values(tables, id_, idname="id"):
    sets = tuple()
    for table in tables:
        sets += (_equals(table + "." + idname, id_),)
    return _AND(*sets)
    
def _count():
    return "COUNT(*)"

def _no_where():
    return "1"

_select_sql_template = "SELECT %s FROM %s WHERE %s"
_update_sql_template = "UPDATE %s SET %s WHERE %s"

def _select_sql(fieldlist, table, where):
    return _select_sql_template % (fieldlist, table, where)

def _update_sql(valuedict, table, where):
    return _update_sql_template % (table, valuedict, where)
#---

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InvalidRowError(Error):
    """Exception raised when an invalid TableRow is requested."""
    def __init__(self, rowname):
        self.rowname = rowname
    def __str__(self):
        return repr(self.rowname)
    
class InvalidFieldError(Error):
    """Exception raised when an invalid TableRow is requested."""
    def __init__(self, columnname):
        self.columnname = columnname
    def __str__(self):
        return repr(self.columnname)

class Cache:
    """
    Generic class/function cache

    Calls a callable and keeps the result for further use in a dictionary.
    If an instance with the same initial arguments already exists, it will
    return the existing result. Supports in-place substitution with an
    existing class.
    """
    # Should this go in pyutil?
    # Question: Which if any of the below classes would benefit from this?
    # None currently have any stored state, but that may change in the future.

    def __init__(self, call):
        self.__call = call
        self.__results = dict()

    def __call__(self, *args, **kwds):
        return self.get(*args, **kwds)

    def get(self, *args, **kwds):
        totalargs = args + tuple(kwds.keys()) + tuple(kwds.values())
        if not self.__results.has_key(totalargs):
            self.__results[totalargs] = self.__call(*args, **kwds)
        return self.__results[totalargs]

class Queue:
    
    """
    Generic queue

    FIFO queue for calls with args. Call add with functions and arguments, and 
    then use it's methods to run the queued up functions.
    """
            
    def __init__(self):
        self.__tasks = list()
    
    def add(self, call, *args, **kwds):
        self.__tasks.append((call,args,kwds))
        
    def pop(self):
        call, args, kwds = self.__tasks.pop(0)
        call(*args, **kwds)
        
    def flush(self):
        for call, args, kwds in self.__tasks:
            call(*args, **kwds)     
        
class Database:
    def __init__(self, conn, debug = 0):
        self.__conn = conn
        self.__field_map = FieldMap(self)
        self.__class_tree = ClassTree(self)
        self.__debug = debug

    def get_table(self, name, idname = "id"):
        """Get Table object by name."""
        return Table(self, name, idname)

    def get_multiple_tables(self, names, idname = "id"):
        """Get MultipleTable object by a tuple of names."""
        return MultipleTable(self, names, idname)

    def get_field_map_tables(self, names, idname = "id"):
        """Get FieldMapTable object by a tuple of names."""
        return FieldMapMultipleTable(self, names, idname)

    def get_gizmo_by_id(self, gid):
        """Get a Gizmo and return an object."""
        return Gizmo(self, gid)

    def query_one(self, sql):
        c = self.__try_execute(sql)
        return _simplify_list(c.fetchone())
    
    def query_all(self, sql):
        c = self.__try_execute(sql)
        return _simplify_list(c.fetchall())

    def execute(self, sql):
        self.__try_execute(sql)
        return True

    def __try_execute(self, sql):
        if self.__debug:
            print sql
        c = self.__conn.cursor()
        try:
            c.execute(sql)
        except PgSQL.libpq.OperationalError:
            print "SQL call failed: " + sql
            # FIXME: Fall back here?
            raise
        return c


    def __get_conn(self):
        return self.__conn

    def __get_field_map(self):
        return self.__field_map
    
    def __get_class_tree(self):
        return self.__class_tree

    connection = property(__get_conn, doc="Connection object for the Database.")
    field_map = property(__get_field_map, doc="FieldMap of the Database.")
    class_tree = property(__get_class_tree, doc="FieldMap of the Database.")

class Table:
    """Generates queries for a table."""
    def __init__(self, db, table, idname = "id"):
        self.__db = db
        self.__table = table
        self.__idname = idname

    def get_row(self, id_):
        return TableRow(self, id_, self.__idname)

    def get_by_id(self, id_, fieldlist):
        return self.select_by_id(id_, _fields(fieldlist))

    def get_all(self, id_):
        return self.select("*", _equals(self.__idname, id_))
    
    def set_by_id(self, id_, valuedict):
        return self.update_by_id(id_, _values(valuedict))
    
    def select_by_id(self, id_, fields):
        return self.select(fields, _equals(self.__idname, id_))
    
    def update_by_id(self, id_, values):
        return self.update(values, _equals(self.__idname, id_))
    
    def select(self, fields, where):
        sql = _select_sql(fields, self.table, where)
        return self.__db.query_one(sql)
    
    def update(self, values, where):
        sql = _update_sql(values, self.__table, where)
        return self.__db.execute(sql)
        
    def __get_table(self):
        return self.__table

    def __get_database(self):
        return self.__db

    table = property(__get_table, doc="Name of Table in the Database.")
    database = property(__get_database, doc="Database containing the Table.")

class MultipleTable:
    """Generates queries spanning multiple tables."""
    def __init__(self, db, tables, idname = "id"):
        self.__db = db
        self.__tables = tables
        self.__idname = idname

    def get_row(self, id_):
        # TableRow can stay unchanged because it just wraps the Table object given to it.
        return TableRow(self, id_, self.__idname)

    def get_by_id(self, id_, fieldlist):
        return self.select_by_id(id_, _fields(fieldlist))    
        
    def set_by_id(self, id_, valuedict):
        #self.update_by_id(id_, _values(valuedict))
        #self.__db.execute(sql)
        # Split up by table, and UPDATE tables one at a time
        tablevalues = dict()
        for item in valuedict.iteritems():
            table, field = item[0].split(".")
            if not tablevalues.has_key(table):
                tablevalues[table] = dict()
            tablevalues[table][field] = item[1]
        for table, fields in tablevalues.iteritems():
            sql = _update_sql(_values(fields), table, _equals(self.__idname, id_))
            self.__db.execute(sql)
        return True
    
    def select_by_id(self, id_, fields):
        return self.select(fields, _id_values(self.__tables, id_, self.__idname))
    
    def update_by_id(self, id_, values):
        return self.update(values, _id_values(self.__tables, id_, self.__idname))
    
    def select(self, fields, where):
        sql = _select_sql(fields, _tables(self.__tables), where)
        return self.__db.query_one(sql)
        
    def update(self, values, where):
        #sql = _multiple_update_sql(valuedict, self.__tables, _id_values(self.tables, id_, self.__idname))
        #return self.__db.execute(sql)
        sql = _update_sql(values, _tables(self.__tables), where)
        self.__db.execute(sql)
        
    def __get_tables(self):
        return self.__tables

    def __get_database(self):
        return self.__db

    tables = property(__get_tables, doc="Names of Tables in the Database.")
    database = property(__get_database, doc="Database containing the Tables.")

class FieldMapMultipleTable(MultipleTable):
    """Represents multiple Tables and looks up field name mapping using the FGDB fieldMap."""

    def __init__(self, db, tables, idname = "id"):
        MultipleTable.__init__(self, db, tables, idname)

    def get_by_id(self, id_, fieldlist):
        return MultipleTable.get_by_id(self, id_, self.database.field_map.process_field_list(self.tables, fieldlist))

    def set_by_id(self, id_, valuedict):
        return MultipleTable.set_by_id(self, id_, self.database.field_map.process_value_dict(self.tables, valuedict))

class TableRow:
    def __init__(self, tb, id_, idname = "id"):
        self.__tb = tb
        self.__id = id_
        if not self.__get_exists(): raise InvalidRowError(self.__id)

    def __get_exists(self):
        if self.__tb.select_by_id(self.__id, _count())==0:
            return False
        else:
            return True
        
    def get(self, *fieldlist):
        return self.__tb.get_by_id(self.__id, fieldlist)

    def set(self, valuedict=None, **keywordvaluedict):
        if valuedict!=None:
            vd = valuedict
        else:
            vd = keywordvaluedict
        return self.__tb.set_by_id(self.__id, vd)

    def __get_table(self):
        return self.__tb

    def __get_id(self):
        return self.__id

    id = property(__get_id, doc="ID of the TableRow.")
    table = property(__get_table, doc="Table containing the TableRow.")

class FieldMapTableRow(TableRow):

    #XXX: needs autocommit somewhere

    def __init__(self, tb, id_, idname = "id"):
        TableRow.__init__(self,tb,id_,idname)
        fields = self.table.database.field_map.get_fields(self.table.tables)
    	values = TableRow.get(self, *fields)
    	self.data = dict()
    	for i in range(len(fields)):
    	    self.data[fields[i]] = values[i]
    	    
    def __getitem__(self, key):
        if key in self.data.keys():
    	    return self.data[key]
    	else:
    	    raise KeyError, key
        
    def __setitem__(self, key, value):
    	if key in self.data.keys():
    	    self.data[key] = value
    	else:
    	    raise KeyError, key
    
    def get(self, *fieldlist):
        # Crazy mess to get multiple fields from a dictionary
        return _simplify_list(tuple(map(self.data.get, fieldlist)))
    
    def set(self, valuedict=None, **keywordvaluedict):
    	if valuedict!=None:
            vd = valuedict
        else:
            vd = keywordvaluedict
    	self.data.update(vd)
    	return True
    
    def commit(self):
    	TableRow.set(self, self.data)
    	return True

class Gizmo(FieldMapTableRow):
    def __init__(self, db, gid):
        # This is where I was planning to use Cache; is it bad to be passing each Gizmo a different Table instance? I think it is (bad)...
        # Chicken and the Egg: Needs class_tree to initialize TableRow, TableRow needs to be initialized to get class_tree. I'll make it create a temporary tablerow and then use that to initialize TableRow.
        temptablerow = TableRow(db.get_table("Gizmo"), gid)
        class_tree = tuple(temptablerow.get("classTree").split("."))
        FieldMapTableRow.__init__(self, db.get_field_map_tables(class_tree), gid)

    def __get_class_tree(self):
        return self.get("classTree")

    class_tree = property(__get_class_tree, doc="Class Tree of the Gizmo.")

class FieldMap(Table):
    def __init__(self, db):
        Table.__init__(self, db, "FieldMap")

    def __get_location(self, classes, fieldname):
        """Return Table fieldname belongs to."""
        sql = _select_sql("tableName", "fieldMap", _AND(_IN("tableName", _string_list(classes)), _equals("fieldName",fieldname)))
	tablename = self.database.query_one(sql)
        if not tablename:
            raise InvalidFieldError(fieldname)
        return tablename

    # Cache stuff
    __get_location_cache = Cache(__get_location)

    def get_location(self, classes, fieldname):
         return self.__get_location_cache(self, classes, fieldname)

    def get_fields(self, classes):
        sql = _select_sql("fieldName", "fieldMap", _IN("tableName", _string_list(classes)))
        fields = self.database.query_all(sql)
        return _single_tuple_list(fields)

    def process_field_list(self, classes, fieldlist):
        """Convert a list like ("id","speed") to ("Gizmo.id","CDDrive.speed")"""
        newfieldlist = tuple()
        for f in fieldlist:
            if not f.count(".")==1:
                newfieldlist += (self.get_location(classes, f) + "." + f,)
            else:
                newfieldlist += (f,)
        return newfieldlist

    def process_value_dict(self, classes, valuedict):
        """Convert a dictionary like {"id":12345,"speed":4} to {"Gizmo.id":12345,"CDDrive.speed":4}"""
        newvaluedict = dict()
        for field, value in valuedict.iteritems():
            if not field.count(".")==1:
                newvaluedict[self.get_location(classes, field) + "." + field] = value
            else:
                newvaluedict[field] = value
        	return newvaluedict

class ClassTree(Table):
    def __init__(self, db):
        Table.__init__(self, db, "classTree")
    
    def __get_location(self, classtree):
        sql = _select_sql("tableName", "classTree", _equals("classTree",classtree))
        return self.database.query_one(sql)

    def get_location(self, classtree):
        return self.__get_location_cache(self, classtree)
    
    def get_list(self):
        sql = _select_sql("classTree", "classTree", _no_where())
        result = self.database.query_all(sql) 
        return _single_tuple_list(result)
        
__all__ = ["connect", "Database", "Table", "TableRow", "MultipleTableRow", "Gizmo", "FieldMap", "ClassTree"]
