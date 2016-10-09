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
    assert tracker(np.sqrt.__acorn__) in ["numpy.sqrt", "numpy.matlib.sqrt"]

def test_dbdir():
    """Tests resetting the database directory manually.
    """
    from acorn.logging.database import dbdir, set_dbdir, _dbdir
    odbdir = dbdir
    set_dbdir(None)
    configured = _dbdir()
    
    from os import path, name
    from acorn.utility import reporoot
    if name != "nt":
        assert configured == path.join(reporoot, "tests", "dbs")
    set_dbdir(odbdir)    

def test_options():
    """Tests getting of database options from using the generic function.
    """
    from acorn.logging.database import TaskDB
    assert TaskDB.get_option("folder") == "./tests/dbs"
    assert TaskDB.get_option("folder", cast=str) == "./tests/dbs"
    
def test_listproj():
    """Tests the listing of projects and tasks in the database directory.
    """
    from acorn.logging.database import list_tasks
    from acorn.utility import abspath
    tasks = list_tasks(abspath("./tests/dbs"))
    assert tasks == {'default': ['default'], 'haul': ['bcs'], 'acorn': ['x']}
