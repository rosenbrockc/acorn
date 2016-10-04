"""Methods that are called by all the sub-package testing modules.
"""
def db_init(package, tmpdir):
    """Initializes the database directory and sets the task.

    Args:
        package (str): package (task) name to initialize for.
        tmpdir (py.path.local): temporary directory fixture from pytest.
    """
    from acorn.logging.database import set_dbdir
    sub = tmpdir.mkdir(package)
    set_dbdir(str(sub))

    from acorn import set_task
    set_task("acorn", package)
    return sub

def db_entries(package):
    """Returns the list of entries in the database, sorted by timestamp so that
    they can be tested explicitly.

    Args:
        package (str): package (task) name configured via
          :func:`acorn.set_task`.
    """
    from acorn.logging.database import dbs
    tdb = dbs[("acorn", package)]

    entries = []
    for uid, elist in tdb.entities.items():
        for entry in elist:
            entries.append((uid, entry))

    #Sort the entries by time stamp so that we can compare them properly.
    return (sorted(entries, key=lambda e: e[1]["s"]), tdb.uuids)

def decorate_check(package):
    """Checks to see if the decoration of `package` produced non-zero values for
    decorated, skipped and N/A.

    """    
    from acorn.logging.decoration import _decor_count
    assert package in _decor_count
    assert _decor_count[package][0] > 0
    assert _decor_count[package][1] > 0
    assert _decor_count[package][2] > 0
