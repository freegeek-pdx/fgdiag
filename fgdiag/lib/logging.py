log=list()
_nodes = dict()

printoutput = False
#printoutput = True

def _format(nodes, title, message):
   nodestr = "[%s]" % "|".join([node for node in nodes])
   return "%s %s: %s" % (nodestr, title, message)

class _LogNode:
   """Log Node Class

   Do not instance this class directly; use create_node and child_node
   """
   def __init__(self, basename, description=None, parents=tuple()):
      if not _nodes.has_key(basename):
         _nodes[basename] = 0
         self.name = basename
      else:
         _nodes[basename] += 1
         self.name = basename + str(_nodes[basename])
      if description:
         self.name += "(%s)" % description
      self.nodetree = (parents + (self.name,))
      self.log("Init", "Log Node Created.")

   def __call__(self, title, message):
      self.log(title, message)

   def log(self, title, message):
      data = (self.nodetree, title, message)
      log.append(data)
      if printoutput:
         print _format(*data)

   def child_node(self, name, description=None):
      return _LogNode(name, description, self.nodetree)

_basenode = _LogNode("base")
_basenode("Start", "Logging Started.")

def create_node(name, description=None):
   """Create a new log node."""
   return _basenode.child_node(name, description)
   
def dump():
   """Return a string dump of the log."""
   text = ""
   for nodes, title, message in log:
      text += _format(nodes, title, message)+"\n"
   return text
