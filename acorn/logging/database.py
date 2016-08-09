"""Methods and classes for creating a JSON database from a tree of
calls to methods with various objects passed as arguments.
"""
from uuid import uuid4
oids = {}
"""dict: keys are python :meth:`id` values, values are the Instance
class instances from which JSON database can be constructed.
"""
def tracker(obj):
    """Returns the Instance of the specified object if it is one that
    we track by default.

    Args:
    obj (object): any python object passed as an argument to a method.

    Returns:
    Instance: if the object is trackable, the Instance instance of
    that object; else None.
    """
    global oids
    untracked = (basestring, int, long, float, complex, tuple, list, dict, set)
    if not isinstance(obj, untracked):
        oid = id(obj)
        if oid in oids:
            result = oids[oid]
        else:
            result = Instance(obj)
            oids[oid] = result
        return result
    else:
        return None
    
class Instance(object):
    """Represents a class instance in the current session which can be
    passed as an argument to method calls, or have unbound methods
    called in it.

    Args:
    pid (int): python memory address (returned by :meth:`id`).
    """
    def __init__(self, pid):
        self.pid = pid
        self.uuid = uuid4()
