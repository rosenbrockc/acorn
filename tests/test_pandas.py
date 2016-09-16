"""Tests the decoration and logging of the pandas package by running some common
code lines and checking that the logged entries make sense.
"""
import pytest
@pytest.fixture(scope="module", autouse=True)
def db(request, tmpdir):
    """Creates a sub-directory in the temporary folder for the `pandas` package's
    database logging. Also sets the package and task to `acorn` and `pandas`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("pandas", tmpdir)

def test_decorate():
    """Tests the decoration of the full numpy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.pandas as pd
    from db import decorate_check
    decorate_check("pandas")

def test_readcsv():
    """Tests reading from a CSV file, since it is one of the most common methods
    that gets called on the pandas library.
    """
    import acorn.pandas as pd
    from os import path
    csdf=pd.read_csv(path.join("tests", "darwin.csv"))

    from db import db_entries
    sentries, uuids = db_entries("pandas")

    uid, entry = sentries[-1]
    assert entry["method"] == "pandas.io.parsers.read_csv"
    assert uid in uuids
    assert entry["args"]["__"] == "../../tests/darwin.csv"

    assert uuids[uid]["fqdn"] == "pandas.core.frame.DataFrame"
    assert "columns" in uuids[uid]
    assert uuids[uid]["shape"] == (15, 2)
    assert len(uuids[uid]["columns"]) == 2
    
    #So far, we have been checking the logging directly on the object. We need
    #to make sure that the data was actually writen to file.
    from acorn.logging.database import TaskDB
    tdb = TaskDB()
    assert len(tdb.entities) > 0
    assert len(tdb.uuids) > 0

def test_frametypes():
    """Tests construction of :class:`pandas.Series` and
    :class:`pandas.Index`. :class:`~pandas.Series` and :class:`~pandas.Index` are
    tricky because they alse have `staticmethod` constructors that get called by
    the :class:`pandas.DataFrame` constructor. So we need to test direct
    construction as well.
    """
    #Since we have already tested the writing to disk, we will now disable the
    #writing and just examine the in-memory collections.
    from acorn import set_writeable
    set_writeable(False)

    import acorn.pandas as pd
    ind = pd.Index([1./i for i in range(1, 11)], dtype=float)
    ser = pd.Series(range(2, 12), index=ind)

    from db import db_entries
    sentries, uuids = db_entries("pandas")

    u0, e0 = sentries[-2]
    u1, e1 = sentries[-1]

    assert e0["method"] == "Index.__new__"
    assert e0["args"]["dtype"] == "float"
    assert "len=10" in e0["args"]["__"]
    assert "max=1.0" in e0["args"]["__"]

    assert e1["method"] == "Series.__new__"
    assert e1["args"]["index"] == u0
    assert "list" in e1["args"]["__"]
    assert "len=10" in e1["args"]["__"]
    assert len(e1["code"]) > 0
    
def test_instance():
    """Tests the instance methods :meth:`pandas.DataFrame.apply` using a lambda
    function and :func:`numpy.sqrt`; also tests
    :meth:`pandas.DataFrame.describe` because it has a tricky decorator using
    `staticmethod` (it gets bound as an instance method by the __init__ call on
    the newly constructed :class:`pandas.DataFrame`.
    """
    from numpy import sqrt
    lambfun = lambda x: x**2

    import acorn.pandas as pd
    pdf = pd.DataFrame(range(15,25))
    pdf.apply(lambfun)
    pdf.apply(np.sqrt)
    pdf.describe()

    from db import db_entries
    sentries, uuids = db_entries("pandas")

    u0, e0 = sentries[-4] #Constructor
    u1, e1 = sentries[-3] #lambda apply
    u2, e2 = sentries[-2] #sqrt apply
    u3, e3 = sentries[-1] #describe

    assert e0["method"] == "DataFrame.__new__"
    assert "len=10" in e0["args"]["__"][0]
    assert "max=24" in e0["args"]["__"][0]
    
    assert e1["method"] == "pandas.core.frame.apply"
    assert e1["args"]["__"][0] == u0
    assert e1["args"]["__"][1] == "lambda (x)"
    #For instance methods, the uuid keys in the entries dict are those of the
    #instance that the method was called on.
    assert u1 == u0
    #We don't really do any tests with the timing; so we might as well make sure
    #that it is being saved.
    assert "elapsed" in e1
    assert isinstance(e1["elapsed"], float)

    assert e2["method"] == "pandas.core.frame.apply"
    assert e2["args"]["__"][0] == u0
    assert e2["args"]["__"][1] == "numpy.sqrt"
    assert u2 == u0

    assert e3["method"] == "pandas.core.generic.describe"
    assert e3["args"]["__"][0] == u0
    assert u3 == u0
