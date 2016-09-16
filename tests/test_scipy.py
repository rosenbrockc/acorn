"""Tests the decoration and logging of the scipy package by running some common
code lines and checking that the logged entries make sense.
"""
#Presently, I only test the interpolation because I use it most frequently; as
#bugs are uncovered and fixed, we can add additional tests here.
import pytest
@pytest.fixture(scope="module", autouse=True)
def db(request, tmpdir):
    """Creates a sub-directory in the temporary folder for the `scipy` package's
    database logging. Also sets the package and task to `acorn` and `scipy`
    respectively.

    Returns:
        (py.path.local): representing the sub-directory for the packages JSON
          files.
    """
    from db import db_init
    return db_init("scipy", tmpdir)

def test_decorate():
    """Tests the decoration of the full scipy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.scipy as sp
    from db import decorate_check
    decorate_check("scipy")

#We have to skip this now because of issue #2; otherwise the tests will not
#pass...
@pytest.mark.skip(reason="Issue #2")
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

    u0, e0 = sentries[-4] #array constructor
    u1, e1 = sentries[-3] #hilbert transform
    u2, e2 = sentries[-2] #spline representation
    u3, e3 = sentries[-1] #spline evaluation

    assert e0["method"] == "numpy.core.multiarray.array"
    assert u0 == e0["returns"]
    assert "list" in e0["args"]["__"][0]
    assert "len=15" in e0["args"]["__"][0]

    assert e1["method"] == "scipy.fftpack.pseudo_diffs.hilbert"
    assert u1 == e1["returns"]
    assert e1["args"]["__"][0] == u0
    assert "elapsed" in e1
    assert isinstance(e1["elapsed"], float)

    assert e2["method"] == "scipy.interpolate.fitpack.splrep"
    assert u2 == e2["returns"]
    assert e2["args"]["__"][0] == u0
    assert e0["args"]["__"][1] == u1

    assert e3["method"] == "scipy.interpolate.fitpack.splev"
    assert u3 == e3["returns"]
    assert e3["args"]["__"][0] == u0
    assert e3["args"]["__"][1] == u2
