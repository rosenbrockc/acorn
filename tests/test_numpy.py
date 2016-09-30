"""Tests the decoration and logging of the numpy package by running some common
code lines and checking that the logged entries make sense.
"""
import pytest
import six
@pytest.fixture(scope="module", autouse=True)
def acorndb(request, dbdir):
    """Creates a sub-directory in the temporary folder for the `numpy` package's
    database logging. Also sets the package and task to `acorn` and `numpy`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("numpy", dbdir)

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

    from acorn.importer import reload_cache
    reload_cache()

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
    
    assert sentries[0][1]["m"] == "numpy.core.multiarray.array"
    assert sentries[1][1]["m"] == "numpy.core.multiarray.zeros"
    assert sentries[2][1]["m"] == "numpy.core.multiarray.empty"

    global _uuid_a
    _uuid_a = sentries[0][0]
    arrayarg = sentries[0][1]["a"]["_"][0]
    assert "len=10" in arrayarg
    if six.PY2:
        assert "<type 'list'>" in arrayarg
    else:
        assert "<class 'range'>" in arrayarg
    
    zerosarg = sentries[1][1]["a"]["_"]
    assert "len=2" in zerosarg[0]
    assert "'tuple'>" in zerosarg[0]
    assert zerosarg[1] == "int"

    emptyarg = sentries[2][1]["a"]["_"]
    assert emptyarg[0] == 7
    assert emptyarg[1] == "complex"

    for uid, entry in sentries[0:3]:
        assert uuids[uid]["fqdn"] == "numpy.ndarray"
        #For non-instance methods, the returns uuid should be what we are
        #indexing under, so that the lookups are easier on the presentation
        #layer.
        assert entry["r"] is None

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
    import acorn.numpy as np
    lsp = np.linspace(0, 1, 25)

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entry in the sorted list.
    uid, entry = sentries[-1]
    assert entry["m"] == "numpy.core.function_base.linspace"
    assert entry["a"]["_"] == [0, 1, 25]
    assert entry["r"] is None

def test_instance(a):
    """Tests :class:`numpy.ndarray` instance method call logging.
    """
    import acorn.numpy as np
    b = a.flatten()
    c = b.reshape((5,2))

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entry in the sorted list.
    uidb, entryb = sentries[-2]
    uidc, entryc = sentries[-1]

    assert entryb["m"] == "numpy.ndarray.flatten"
    assert entryb["a"]["_"] == [_uuid_a]
    urb = entryb["r"]

    assert entryc["m"] == "numpy.ndarray.reshape"
    if six.PY2:
        assert entryc["a"]["_"] == [urb, "<type 'tuple'> len=2 min=2 max=5"]
    else:
        assert entryc["a"]["_"] == [urb, "<class 'tuple'> len=2 min=2 max=5"]
    
def test_special(a):
    """Tests :class:`numpy.ndarray` special functions such as __mul__, __div__,
    etc. Also tests the array slicing.
    """
    import acorn.numpy as np
    b = 2*a
    c = a[2:6]/3
    d = a.copy()
    d *= 2

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entries in the sorted list.
    uidb, entryb = sentries[-5]
    uidc, entryc = sentries[-4]
    uidd, entryd = sentries[-3]
    uide, entrye = sentries[-2]
    uidf, entryf = sentries[-1]

    assert entryb["m"] == "numpy.ufunc.multiply"
    assert entryb["a"]["_"] == [2, _uuid_a]

    #We have a getslice and a divide in the variable `c`.
    if six.PY2:
        assert entryc["m"] == "numpy.ndarray.__getslice__"
        assert entryc["a"]["_"] == [_uuid_a, 2, 6]
    else:
        #__getslice__ was deprecated by Py3.
        assert entryc["m"] == "numpy.ndarray.__getitem__"
        assert entryc["a"]["_"] == [_uuid_a, "slice(2, 6, None)"]
    urc = entryc["r"]

    if six.PY2:
        assert entryd["m"] == "numpy.ufunc.divide"
    else:
        #divide was changed by default to be true_divide in Py3.
        assert entryd["m"] == "numpy.ufunc.true_divide"
    assert entryd["a"]["_"] ==  [urc, 3]

    assert entrye["m"] == "numpy.ndarray.copy"
    assert entrye["a"]["_"] == [_uuid_a]
    ure = entrye["r"]

    assert entryf["m"] == "numpy.ufunc.multiply"
    assert uidf == ure
    assert entryf["a"]["_"] == [ure, 2, ure]
    
def test_static(a):
    """Tests the numpy static methods to make sure that they also log correctly.
    """
    import acorn.numpy as np
    b = np.multiply(a, 2)
    c = np.ndarray.reshape(a.flatten(), (5,2))
    d = np.asarray(range(10))
    e = np.delete(b, 2, 0)

    from db import db_entries
    sentries, uuids = db_entries("numpy")

    #Because the tests are executed in the order they are found in this file, we
    #can just look at the *last* entries in the sorted list.
    uidb, entryb = sentries[-5] #multiply
    uidc, entryc = sentries[-4] #flatten
    uidc2, entryc2 = sentries[-3] #reshape
    uidd, entryd = sentries[-2] #asarray
    uide, entrye = sentries[-1] #delete

    assert entryb["m"] == "numpy.multiply"
    assert entryb["a"]["_"] == [_uuid_a, 2]

    #Even though we are explicitly calling the static ndarray.flatten, it has
    #the same net effect as an instance method call on the first array
    #argument. As such, it is treated as an instance method
    assert entryc["m"] == "numpy.ndarray.flatten"
    assert entryc["a"]["_"] == [_uuid_a]
    assert entryc["s"] > 0
    ucr = entryc["r"]

    assert entryc2["m"] == "numpy.ndarray.reshape"
    if six.PY2:
        assert entryc2["a"]["_"] == [ucr, "<type 'tuple'> len=2 min=2 max=5"]
    else:
        assert entryc2["a"]["_"] == [ucr, "<class 'tuple'> len=2 min=2 max=5"]

    assert entryd["m"] == "numpy.core.numeric.asarray"
    if six.PY2:
        assert entryd["a"]["_"] == ["<type 'list'> len=10 min=0 max=9"]
    else:
        assert entryd["a"]["_"] == ["<class 'range'> len=10 min=0 max=9"]

    assert entrye["m"] == "numpy.lib.function_base.delete"
    assert entrye["a"]["_"] == [uidb, 2, 0]

def test_scalar():
    """Makes sure that ufuncs return scalar values for array operations.
    """
    import acorn.numpy as np
    a1 = np.array(0.)
    a2 = np.array(0.025)
    assert np.isscalar(np.sum((a1, a2)))

def test_array():
    """Makes sure that array functions which are *not* ufuncs return arrays.
    """
    import acorn.numpy as np
    assert isinstance(np.squeeze(np.array(0.0), 0), np.ndarray)
