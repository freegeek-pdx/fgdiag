log=[]
module = ""

printoutput = False
printoutput = True

def debug(section, message):
   log.append((module, section,message))
   if printoutput:
       print format(module, section,message)
       
def format(module, section,message):
    return "[%s] %s: %s" % (module, section,message)

def dump():
    text = ""
    for module, section, message in log:
        text += format(module, section,message)+"\n"
    return text

def start(module_):
    global module
    module = module_.upper()
    debug("Start", "Debug started.")
