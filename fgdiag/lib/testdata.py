"""Test data handling"""
# This needs to be used in between FGDB storage and the test script output and use fieldNames for something.

def process(data, fieldmap):
    """Return a modified data, with parameter names replaced with Table locations"""
    newdata = dict()
    for item in data.iteritems():
        tableloc = fieldmap.get_field_location(item[0])
        newdata[tableloc] = item[1]
    return newdata
    
def register_test_data(self, gizmo):
        """Put data into appropriate fields in database."""