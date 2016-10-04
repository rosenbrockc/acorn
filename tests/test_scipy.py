"""Tests the decoration and logging of the scipy package by running some common
code lines and checking that the logged entries make sense.
"""
#Presently, I only test the interpolation because I use it most frequently; as
#bugs are uncovered and fixed, we can add additional tests here.
import pytest
import six
@pytest.fixture(scope="module", autouse=True)
def acorndb(request, dbdir):
    """Creates a sub-directory in the temporary folder for the `scipy` package's
    database logging. Also sets the package and task to `acorn` and `scipy`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("scipy", dbdir)

def test_decorate():
    """Tests the decoration of the full scipy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.scipy as sp
    from db import decorate_check
    from acorn import set_writeable
    set_writeable(False)    
    decorate_check("scipy")

def test_interpolate():
    """Tests spline interpolation and hilbert transform for scipy.
    """
    import acorn.scipy as sp
    from scipy.interpolate import splev, splrep

    #Scipy wraps almost the entire numpy library, so we should have these array
    #calls using scipy logged as well as with numpy.
    a = 2*sp.array(range(15))
    tck = splrep(a, sp.fftpack.hilbert(a))
    y = splev(a, tck)

    from db import db_entries
    sentries, uuids = db_entries("scipy")

    u0, e0 = sentries[-5] #array constructor
    u1, e1 = sentries[-4] #multiplication by 2
    u2, e2 = sentries[-3] #hilbert transform
    u3, e3 = sentries[-2] #spline representation
    u4, e4 = sentries[-1] #spline evaluation

    assert e0["m"] == "numpy.core.multiarray.array"
    if six.PY2:
        assert e0["a"]["_"] == ["<type 'list'> len=15 min=0 max=14"]
    else:
        assert e0["a"]["_"] == ["<class 'range'> len=15 min=0 max=14"]

    assert e1["m"] == "numpy.ufunc.multiply"
    assert e1["a"]["_"] == [2, u0]
    
    assert e2["m"] == "scipy.fftpack.pseudo_diffs.hilbert"
    assert e2["a"]["_"] == [u1]

    assert e3["m"] == "scipy.interpolate.fitpack.splrep"
    assert e3["a"]["_"] == [u1, u2]

    assert e4["m"] == "scipy.interpolate.fitpack.splev"
    assert e4["a"]["_"] == [u1, u3]
