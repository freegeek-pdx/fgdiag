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

class InvalidStatusError(Error):
    """Exception raised when an invalid status is returned by a test."""
    def __init__(self, status):
        self.status = status
    def __str__(self):
        return repr(self.status)