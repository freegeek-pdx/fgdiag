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

	def get_gizmo_by_id(gid):
		"""Get a Gizmo and return an object."""

class Gizmo:
	def register_test_data(data):
		"""Put data into appropriate fields in database"""