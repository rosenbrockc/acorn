"""Tests some of the extra database functionality that doesn't normally show up
in day-to-day use.
"""
import six
def test_tracker():
    """Tests the tracker on some outlier cases.
    """
    from acorn.logging.database import tracker
    if six.PY2:
        assert tracker([]) == "<type 'list'> len=0"
    else:
        assert tracker([]) == "<class 'list'> len=0"
    assert tracker(slice(0, 2, 4)) == "slice(0, 2, 4)"

    import numpy as np
    assert tracker(np.sqrt.__acornext__) == "numpy.sqrt"

def test_dbdir():
    """Tests resetting the database directory manually.
    """
    from acorn.logging.database import dbdir, set_dbdir, _dbdir
    odbdir = dbdir
    set_dbdir(None)
    configured = _dbdir()
    from os import path, name
    if name != "nt":
        assert configured == path.abspath(path.expanduser("~/temp/acorn"))
    set_dbdir(odbdir)    

def test_options():
    """Tests getting of database options from using the generic function.
    """
    from acorn.logging.database import TaskDB
    assert TaskDB.get_option("folder") == "~/temp/acorn"
    assert TaskDB.get_option("folder", cast=str) == "~/temp/acorn"
    
