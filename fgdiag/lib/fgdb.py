
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
import psycopg
from errors import InvalidRowError, InvalidFieldError, SQLError, DBConnectError
from logging import create_node

_log = create_node(__name__)

def connect(host, db, user, passwd):
    """Return a Database instance connected to dburl.

    Attempt to connect to dburl, and fail gracefully by falling back to a temporary file cache.

    """

    try:
        dbstr = "host=%s dbname=%s user=%s password=%s" % (host,db,user,passwd)
        _log("Connect", dbstr)
        conn = psycopg.connect(dbstr)
        # Make it autocommit - Without this changes will not save
        conn.autocommit(True)
        mydb = Database(conn, host, db, user)
        _log("Connect", "Connection Succeeded.")
        
    except Exception, e:
        # (Insert graceful failure here) ;)
        _log("Connect", "Connection Failed.")
        raise DBConnectError(e)

    return mydb

# Utils

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

# SQL Generation

class _SQLList(list):

    def __init__(self, data):
        list.__init__(self, data)

    def __str__(self):
        return ", ".join([str(value) for value in self])

    def __repr__(self):
        return "SQL"+list.__repr__(self)

class _SQLEquals:

    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return "%s = %s" % (self.field, _SQLValue(self.value))

class _SQLFields(_SQLList):

    def __init__(self, data):
        _SQLList.__init__(self, data)

class _SQLValues(_SQLList):

    def __init__(self, data):
        _SQLList.__init__(self, data)

    def __str__(self):
        return "(%s)" % ", ".join([str(_SQLValue(value)) for value in self])

class _SQLTables(_SQLList):

    def __init__(self, data):
        _SQLList.__init__(self, data) 

class _SQLValueDict(dict):

    def __init__(self, data):
        dict.__init__(self, data)

    def __str__(self):
        return str(_SQLList([_SQLEquals(field, value) for field, value in self.iteritems()]))
        
    def to_fields_values(self):
        return _SQLFields(self.keys()), _SQLValues(self.values())

class _SQLAnd(_SQLList):

    def __init__(self, *data):
        _SQLList.__init__(self, data)

    def __str__(self):
        return " AND ".join([str(value) for value in self])

class _SQLOr(_SQLList):

    def __init__(self, *data):
        _SQLList.__init__(self, data)

    def __str__(self):
        return " OR ".join([str(value) for value in self])

class _SQLIn:

    def __init__(self, thing, container):
        self.thing = thing
        self.container = container

    def __str__(self):
        return "%s IN %s" % (self.thing, self.container)

class _SQLWhere(_SQLList):

    def __init__(self, data=["1=1"]):
        _SQLList.__init__(self, data)

class _SQLId:

    def __init__(self, id_):
        try:
            psycopg.INTEGER(str(id_))
        except ValueError:
            raise ValueError("ID value must be a valid integer.")

        self.id = id_

    def __str__(self):
        return str(self.id)

class _SQLValue:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(psycopg.QuotedString(str(self.value)))

    def __repr__(self):
        return str(self.value)

class _SQLCount:

    def __str__(self):
        return "COUNT(*)"

class _SQLSelectNextVal:

    def __init__(self, seq):
        self.seq = seq

    def __str__(self):
        return "SELECT NEXTVAL(%s)" % _SQLValue(self.seq)

class _SQLSelect:

    def __init__(self, table, fields, where):
        self.table = table
        self.fields = fields
        self.where = where

    def __str__(self):
        return "SELECT %s FROM %s WHERE %s" % (self.fields, self.table, self.where)

class _SQLUpdate:

    def __init__(self, table, fieldvalues, where):
        self.table = table
        self.fieldvalues = fieldvalues
        self.where = where

    def __str__(self):
        return "UPDATE %s SET %s WHERE %s" % (self.table, self.fieldvalues, self.where)

class _SQLInsert:

    def __init__(self, table, fields, values):
        self.table = table
        self.fields = fields
        self.values = values

    def __str__(self):
        # Parens only for fields, because values already makes them
        return "INSERT INTO %s (%s) VALUES %s" % (self.table, self.fields, self.values)

# Shortcuts

def _id_equals(idname, id_):
    return _SQLEquals(idname, _SQLId(id_))

def _id_values(tables, id_, idname="id"):
    return _SQLAnd(*[_id_equals("%s.%s" % (table, idname), id_) for table in tables])

#---

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
    def __init__(self, conn, host, dbname, user):
        self.__conn = conn
        self.__field_map = FieldMap(self)
        self.__class_tree = ClassTree(self)
        self.__host = host
        self.__dbname = dbname
        self.__user = user
        self.__log = _log.child_node("Database", "%s@%s/%s" % (self.__user, self.__host, self.__dbname))

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

    def add_gizmo(self, classtree):
        self.__log("Create Gizmo", "Fetching new Gizmo ID.")
        gid = self.query_one(_SQLSelectNextVal("gizmo_id_seq"))
        self.__log("Create Gizmo", "New Gizmo ID is %s." % gid)
        # Not going to try to use MultipleTable... too crazy already
        classtreelist = classtree.split(".")
        for gizmoclass in classtreelist:
            tb = self.get_table(gizmoclass)
            tb.add_row(gid, {"classtree":classtree})
        self.__log("Create Gizmo", "Gizmo created successfully.")
        return gid

    def query_one(self, sql):
        c = self.__try_execute(sql)
        return _simplify_list(c.fetchone())
    
    def query_all(self, sql):
        c = self.__try_execute(sql)
        return _simplify_list(c.fetchall())

    def execute(self, sql):
	c = self.__try_execute(sql)
	return True

    def __try_execute(self, sql):
        sql = str(sql)
        self.__log("SQL Call", sql)
        c = self.__conn.cursor()
        try:
            c.execute(sql)
        except psycopg.ProgrammingError, e:
            # print "SQL call failed: " + sql
            # FIXME: Fall back here?
            self.__log("SQL Call", "SQL Call Failed: \"%s\"" % str(e).replace("\n",", "))
            raise SQLError(sql, e)
        return c

    def __get_conn(self):
        return self.__conn

    def __get_field_map(self):
        return self.__field_map
    
    def __get_class_tree(self):
        return self.__class_tree

    def __get_host(self):
        return self.__host

    def __get_dbname(self):
        return self.__dbname

    def __get_user(self):
        return self.__user


    connection = property(__get_conn, doc="Connection object for the Database.")
    field_map = property(__get_field_map, doc="FieldMap of the Database.")
    class_tree = property(__get_class_tree, doc="FieldMap of the Database.")
    host = property(__get_host, doc="Host of the Database connection.")
    dbname = property(__get_dbname, doc="Database name of the Database connection.")
    user = property(__get_user, doc="User name of the Database connection.")

class Table:
    """Generates queries for a table."""
    def __init__(self, db, table, idname = "id"):
        self.__db = db
        self.__table = table
        self.__idname = idname
        
    def get_row(self, id_):
        # TableRow can stay unchanged because it just wraps the Table object given to it.
        return TableRow(self, id_, self.__idname)

    def add_row(self, id_, valuedict):
        vd = _SQLValueDict(valuedict)
        vd[self.__idname] = id_
        self.insert(*vd.to_fields_values())

    def get_by_id(self, id_, fieldlist):
        return self.select_by_id(id_, _SQLFields(fieldlist))

    def get_all(self, id_):
        return self.select_by_id("*")
    
    def set_by_id(self, id_, valuedict):
        return self.update_by_id(id_, _SQLValueDict(valuedict))
    
    def select_by_id(self, id_, fields):
        return self.select(fields, _id_equals(self.__idname, id_))

    def get_exists_by_id(self, id_):
        if self.select_by_id(id_, _SQLCount())==0:
            return False
        else:
            return True
    
    def update_by_id(self, id_, values):
        return self.update(values, _id_equals(self.__idname, id_))
    
    def select(self, fields, where):
        sql = self.select_sql(fields, where)
        return self.__db.query_one(sql)
    
    def update(self, fieldvalues, where):
        sql = self.update_sql(fieldvalues, where) 
        return self.__db.execute(sql)

    def insert(self, fields, values):
        sql = self.insert_sql(fields, values)
        return self.__db.execute(sql)

    def select_sql(self, fields, where):
        return _SQLSelect(self.table, fields, where)

    def update_sql(self, fieldvalues, where):
        return _SQLUpdate(self.__table, fieldvalues, where)

    def insert_sql(self, fields, values):
        return _SQLInsert(self.__table, fields, values)
        
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
        return self.select_by_id(id_, _SQLFields(fieldlist))    
        
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
        for table, tablevaluedict in tablevalues.iteritems():
            sql = _SQLUpdate(table, _SQLValueDict(tablevaluedict),  _id_equals(self.__idname, id_))
            self.__db.execute(sql)
        return True
    
    def select_by_id(self, id_, fields):
        return self.select(fields, _id_values(self.__tables, id_, self.__idname))

    def get_exists_by_id(self, id_):
        if self.select_by_id(id_, _SQLCount())==0:
            return False
        else:
            return True
    
    def update_by_id(self, id_, values):
        return self.update(values, _id_values(self.__tables, id_, self.__idname))
    
    def select(self, fields, where):
        sql = self.select_sql(fields, where)
        return self.__db.query_one(sql)
        
    def update(self, fieldvalues, where):
        #sql = _multiple_update_sql(valuedict, self.__tables, _id_values(self.tables, id_, self.__idname))
        #return self.__db.execute(sql)
        sql = self.update_sql(fields, where)
        self.__db.execute(sql)

    def select_sql(self, fields, where):
        return _SQLSelect(_SQLTables(self.__tables), fields, where)

    def update_sql(self, fieldvalues, where):
        return _SQLUpdate(_SQLTables(self.__tables), fieldvalues, where)
      
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
        if not tb.get_exists_by_id(id_): raise InvalidRowError(id_)
        self.__tb = tb
        self.__id = id_
        
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
        temptablerow = db.get_table("Gizmo").get_row(gid)
        class_tree = tuple(temptablerow.get("classTree").split("."))
        FieldMapTableRow.__init__(self, db.get_field_map_tables(class_tree), gid)
        self.__log = _log.child_node("Gizmo", gid)

    def __get_class_tree(self):
        return self.get("classTree")

    class_tree = property(__get_class_tree, doc="Class Tree of the Gizmo.")

class FieldMap(Table):
    def __init__(self, db):
        Table.__init__(self, db, "fieldMap")

    def __get_location(self, classes, fieldname):
        """Return Table fieldname belongs to."""
        tablename = self.select("tableName", _SQLAnd(_SQLIn("tableName", _SQLValues(classes)), _SQLEquals("fieldName",fieldname)))
        if not tablename:
            raise InvalidFieldError(fieldname)
        return tablename

    # Cache stuff
    __get_location_cache = Cache(__get_location)

    def get_location(self, classes, fieldname):
         return self.__get_location_cache(self, classes, fieldname)

    def get_fields(self, classes):
        sql = self.select_sql("fieldName", _SQLIn("tableName", _SQLValues(classes)))
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
        return self.select("tableName", _SQLEquals("classTree",classtree))

    def get_location(self, classtree):
        return self.__get_location_cache(self, classtree)
    
    def get_list(self):
        sql = self.select_sql("classTree", _SQLWhere())
        print sql
        result = self.database.query_all(sql) 
        return _single_tuple_list(result)
        
__all__ = ["connect", "Database", "Table", "TableRow", "MultipleTableRow", "Gizmo", "FieldMap", "ClassTree"]
