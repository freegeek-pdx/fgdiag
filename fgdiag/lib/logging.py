import atexit, time

_nodenames = dict()

def _format(timestamp, nodes, title, message):
   nodestr = "[%s]" % "|".join([node for node in nodes])
   return "[%s]: %s %s: %s" % (time.asctime(time.localtime(timestamp)), nodestr, title, message)

class _LogReceptor:
   """Log Receptor Class

   Template for pluggable outputs for logs.
   """
   
   def log(self, data):
      raise NotImplementedError

   def exit(self, log):
      raise NotImplementedError

class BaseReceptor(_LogReceptor):
   """Keeps track of log and receptors, and alerts their hooks."""
   def __init__(self):
      self.fulllog = list()
      self.receptors = dict()

   def add_receptor(self, name, receptor):
      self.receptors[name] = receptor

   def remove_receptor(self, name):
      del self.receptors[name]
   
   def log(self, data):
      self.fulllog.append(data)
      for receptor in self.receptors.itervalues():
         try:
            receptor.log(data)
         except:
            # Log something?
            raise

   def exit(self):
      for receptor in self.receptors.itervalues():
         try:
            receptor.exit(self.log)
         except:
            # Log something?
            raise
         
class PrintReceptor(_LogReceptor):
   def log(self, data):
      print _format(*data)

   def exit(self, log):
      pass

_basereceptor = BaseReceptor()

add_receptor = _basereceptor.add_receptor
remove_receptor = _basereceptor.remove_receptor

# For Debug
#add_receptor("print", PrintReceptor())

class _LogNode:
   """Log Node Class

   Do not instance this class directly; use create_node and child_node
   """
   def __init__(self, basename, description=None, parents=tuple(), noreceptors=False):
      if not _nodenames.has_key(basename):
         _nodenames[basename] = 0
         self.name = basename
      else:
         _nodenames[basename] += 1
         self.name = basename + str(_nodenames[basename])
      if description:
         self.name += "(%s)" % description
      self.nodetree = (parents + (self.name,))
      self.noreceptors = noreceptors
      self.log("Init", "Log Node Created.")

   def __call__(self, title, message):
      self.log(title, message)

   def log(self, title, message):
      data = (time.time(), self.nodetree, title, message)
      if not self.noreceptors:
         _basereceptor.log(data)
      
   def child_node(self, name, description=None):
      return _LogNode(name, description, self.nodetree)

def create_node(name, description=None):
   """Create a new log node."""
   return _basenode.child_node(name, description)
   
def dump():
   """Return a string dump of the log."""
   text = ""
   for timestamp, nodes, title, message in log:
      text += _format(timestamp, nodes, title, message)+"\n"
   return text

_basenode = _LogNode("base")
_basenode("Start", "Logging Started.")

def exit():
   global _basenode
   global _basereceptor
   
   _basereceptor.exit()
      
   _basenode("Finish", "Logging Finished")

   del _basenode
   # Save log?

atexit.register(exit)
