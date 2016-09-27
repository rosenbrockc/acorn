"""Tests the decoration and logging of the numpy package by running some common
code lines and checking that the logged entries make sense.
"""
import pytest
@pytest.fixture(scope="module", autouse=True)
def db(request, tmpdir):
    """Creates a sub-directory in the temporary folder for the `numpy` package's
    database logging. Also sets the package and task to `acorn` and `numpy`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("numpy", tmpdir)

@pytest.fixture(scope="module")
def a(request):
    """Initializes the standard array `a` that most of the tests reference. This
    makes it so that we don't have to re-check the log every time we create a
    new `a` instance.

    Returns:
        (numpy.ndarray): initialized from range(10).
    """
    import acorn.numpy as np
    return np.array(range(10))

def test_decorate():
    """Tests the decoration of the full numpy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.numpy as np
    from db import decorate_check
    decorate_check("numpy")

_uuid_a = None
"""str: uuid of the fixture 'a' so that we can make sure it is referenced
correctly in subsequent tests.
"""
    
def test_arraylike(a):
    """Tests logging on array initialization using :func:`numpy.array`,
    :func:`numpy.zeros`, and :func:`numpy.empty`.
    """
    import acorn.numpy as np
    z = np.zeros((5, 2), int)
    e = np.empty(7, complex)

    #Now, we check the logging to make sure that each of these generated an
    #entry in the log. We call cleanup to make sure that any pending entries get
    #written to disk.
    from acorn.logging.database import cleanup
    cleanup()

    from acorn.logging.database import dbs
    from db import db_entries
    assert ("acorn", "numpy") in dbs
    sentries, uuids = db_entries("numpy")
    
    assert sentries[0][1]["method"] == "numpy.core.multiarray.array"
    assert sentries[1][1]["method"] == "numpy.core.multiarray.zeros"
    assert sentries[2][1]["method"] == "numpy.core.multiarray.empty"

    global _uuid_a
    _uuid_a = sentries[0][0]
    arrayarg = sentries[0][1]["args"]["__"][0]
    assert "len=10" in arrayarg
    assert "<type 'list'>" in arrayarg

    zerosarg = sentries[1][1]["args"]["__"]
    assert "len=2" in zerosarg[0]
    assert "<type 'tuple'>" in zerosarg[0]
    assert zerosarg[1] == "int"

    emptyarg = sentries[1][1]["args"]["__"]
    assert emptyarg[0] == 7
    assert emptyarg[1] == "complex"

    for uid, entry in sentries[0:3]:
        assert uuids[uid]["fqdn"] == "numpy.ndarray"
        #For non-instance methods, the returns uuid should be what we are
        #indexing under, so that the lookups are easier on the presentation
        #layer.
        assert entry["returns"] is None

    #So far, we have been checking the logging directly on the object. We need
    #to make sure that the data was actually writen to file.
    from acorn.logging.database import TaskDB
    tdb = TaskDB()
    assert len(tdb.entities) > 0
    assert len(tdb.uuids) > 0

def test_linspace():
    """Tests :func:`numpy.linspace` to make sure it logs correctly.
    """
    #Since we have already tested the writing to disk, we will now disable the
    #writing and just examine the in-memory collections.
    from acorn import set_writeable
    set_writeable(False)
    
    import acorn.numpy as np
    lsp = np.linspace(0, 1, 25)

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entry in the sorted list.
    uid, entry = sentries[-1]
    assert entry["method"] == "numpy.core.function_base.linspace"
    assert entry["args"]["__"] == [0, 1, 25]
    assert entry["returns"] is None

def test_instance(a):
    """Tests :class:`numpy.ndarray` instance method call logging.
    """
    from acorn import set_writeable
    set_writeable(False)
    
    import acorn.numpy as np
    b = a.flatten()
    c = b.reshape((5,2))

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entry in the sorted list.
    uidb, entryb = sentries[-2]
    uidc, entryc = sentries[-1]
    
    assert entryb["method"] == "numpy.ndarray.flatten"
    assert entryb["args"]["__"] == [uidb]
    assert entryb["code"] > 0

    assert entryc["method"] == "numpy.ndarray.reshape"
    assert entryc["args"]["__"] == [uidb, "<type 'tuple'> len=2 min=2 max=5"]
    assert len(entryc["code"] > 0)
    
def test_special():
    """Tests :class:`numpy.ndarray` special functions such as __mul__, __div__,
    etc. Also tests the array slicing.
    """
    from acorn import set_writeable
    set_writeable(False)
    
    import acorn.numpy as np
    b = 2*a
    c = a[2:6]/3
    a *= 2

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entries in the sorted list.
    uidb, entryb = sentries[-4]
    uidc, entryc = sentries[-3]
    uidd, entryd = sentries[-2]
    uide, entrye = sentries[-1]
    
    assert entryb["method"] == "numpy.ufunc.multiply"
    assert entryb["args"]["__"] == [2, _uuid_a]
    assert entryb["code"] > 0

    #We have a getslice and a divide in the variable `c`.
    assert entryc["method"] == "numpy.ndarray.__getslice__"
    assert entryc["args"]["__"] == [_uuid_a, 2, 6]
    assert len(entryc["code"] > 0)

    assert entryd["method"] == "numpy.ufunc.divide"
    assert entryd["args"]["__"] ==  [uidc, 3]

    assert entrye["method"] == "numpy.ufunc.multiply"
    assert uide == _uuid_a
    assert entrye["args"]["__"] == [_uuid_a, 2, _uuid_a]
    
def test_static(a):
    """Tests the numpy static methods to make sure that they also log correctly.
    """
    from acorn import set_writeable
    set_writeable(False)
    
    import acorn.numpy as np
    b = np.multiply(a, 2)
    c = np.ndarray.reshape(a.flatten(), (5,2))
    d = np.asarray(range(10))
    e = np.delete(b, 2, 0)

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entries in the sorted list.
    uidb, entryb = sentries[-4]
    uidc, entryc = sentries[-3]
    uidc2, entryc2 = sentries[-2]
    uide, entrye = sentries[-1]
    
    assert entryb["method"] == "numpy.ufunc.multiply"
    assert entryb["args"]["__"] == [_uuid_a, 2]
    assert entryb["code"] > 0

    assert entryc["method"] == "numpy.ndarray.flatten"
    assert entryc["args"]["__"] == [_uuid_a]
    assert entryc["code"] > 0
    assert entryc["start"] > 0
    
    assert entryc2["method"] == "numpy.ndarray.reshape"
    assert entryc2["args"]["__"] == [uidc, "<type 'tuple'> len=2 min=2 max=5"]
    assert entryc2["code"] > 0

    assert entrye["method"] == "numpy.lib.function_base.delete"
    assert entrye["args"]["__"] == [uidb, 2, 0]
    assert entrye["code"] > 0
    assert entrye["elapsed"] > 0    

def test_scalar():
    """Makes sure that ufuncs return scalar values for array operations.
    """
    a1 = np.array(0.)
    a2 = np.array(0.025)
    assert np.isscalar(np.sum(a1, a2))

def test_array():
    """Makes sure that array functions which are *not* ufuncs return arrays.
    """
    assert isinstance(np.squeeze(np.array(0.0), 0))
