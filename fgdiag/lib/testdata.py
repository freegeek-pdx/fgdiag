"""Test database handling"""

def register_test_data(gizmo, data):
    """Put data into appropriate fields in database."""
    gizmo.set(data)
    # Set the testData field?
    #gizmo.set(testData=True)