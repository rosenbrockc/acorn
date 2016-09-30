"""Tests the decoration and logging of the pandas package by running some common
code lines and checking that the logged entries make sense.
"""
import pytest
import six
@pytest.fixture(scope="module", autouse=True)
def acorndb(request, dbdir):
    """Creates a sub-directory in the temporary folder for the `pandas` package's
    database logging. Also sets the package and task to `acorn` and `pandas`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("pandas", dbdir)

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
    assert entry["m"] == "pandas.io.parsers.read_csv"
    assert uid in uuids
    assert entry["a"]["_"] == ["tests/darwin.csv"]

    assert uuids[uid]["fqdn"] == "pandas.core.frame.DataFrame"
    assert "columns" in uuids[uid]
    assert uuids[uid]["shape"] == (15, 2)
    assert len(uuids[uid]["columns"]) == 2
    
    #So far, we have been checking the logging directly on the object. We need
    #to make sure that the data was actually writen to file.
    from acorn.logging.database import dbs
    tdb = dbs[("acorn", "pandas")]
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
    import acorn.pandas as pd
    ind = pd.Index([1./i for i in range(1, 11)], dtype=float)
    ser = pd.Series(range(2, 12), index=ind)

    from db import db_entries
    sentries, uuids = db_entries("pandas")

    u0, e0 = sentries[-2]
    u1, e1 = sentries[-1]

    assert e0["m"] == "pandas.indexes.base.Index.__new__"
    assert e0["a"]["dtype"] == "float"
    assert "len=10" in e0["a"]["_"][0]
    assert "max=1.0" in e0["a"]["_"][0]

    assert e1["m"] == "pandas.core.series.Series.__new__"
    assert e1["a"]["index"] == u0
    if six.PY2:
        assert e1["a"]["_"] == ["<type 'list'> len=10 min=2 max=11"]
    else:
        assert e1["a"]["_"] == ["<class 'range'> len=10 min=2 max=11"]
    
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
    import acorn.numpy as np
    if six.PY2:
        pdf = pd.DataFrame(range(15,25))
    else:
        pdf = pd.DataFrame(data=list(range(15,25)))
    pdf.apply(lambfun)
    pdf.apply(np.sqrt)
    pdf.describe()

    from db import db_entries
    sentries, uuids = db_entries("pandas")

    u0, e0 = sentries[-4] #Constructor
    u1, e1 = sentries[-3] #lambda apply
    u2, e2 = sentries[-2] #sqrt apply
    u3, e3 = sentries[-1] #describe

    #pandas in python 3 requires us to name the data keyword argument; it
    #doesn't automatically splice it into the first position.
    assert e0["m"] == "pandas.core.frame.DataFrame.__new__"
    if six.PY2:
        assert e0["a"]["_"] == ["<type 'list'> len=10 min=15 max=24"]
    else:
        assert e0["a"]["data"] == "<class 'list'> len=10 min=15 max=24"
    
    assert e1["m"] == "pandas.core.frame.apply"
    assert e1["a"]["_"][0] == u0
    assert e1["a"]["_"][1] == "lambda (x)"
    #For instance methods, the uuid keys in the entries dict are those of the
    #instance that the method was called on.
    assert u1 == u0

    assert e2["m"] == "pandas.core.frame.apply"
    assert e2["a"]["_"][0] == u0
    #Unfortunately, the order in which members of a package is returned is not
    #always deterministic, so numpy.sqrt may be first picked up by
    #numpy.matlib.sqrt.
    assert (e2["a"]["_"][1] == "numpy.sqrt" or
            e2["a"]["_"][1] == "numpy.matlib.sqrt")
    assert u2 == u0

    assert e3["m"] == "pandas.core.generic.describe"
    assert e3["a"]["_"][0] == u0
    assert u3 == u0
