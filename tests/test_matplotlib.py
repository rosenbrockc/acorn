"""Tests the basic plotting functionality in `matplotlib` for decoration with
`acorn`.
"""
import pytest
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
    return db_init("matplotlib", dbdir)

# def test_decorate():
#     """Tests the decoration of the full scipy module. Since the module can
#     change, the exact number of methods and objects decorated will be constantly
#     changing. Instead, we just make sure that some were decorated, skipped and
#     N/A in the module statistics.
#     """
#     import acorn.matplotlib as mpl
#     from db import decorate_check
#     decorate_check("matplotlib")

# def test_plot():
#     """Tests a basic plot for logging functionality. We could definitely use
#     more tests for the different kinds of plots.
#     """
#     import matplotlib.pyplot as plt
#     plt.plot(range(10), range(10))

#     from db import db_entries
#     sentries, uuids = db_entries("matplotlib")

#     u0, e0 = sentries[-1]
#     assert e0["method"] == "matplotlib.pyplot.plot"
#     assert e0["args"]["__"] == ["<type 'list'> len=10 min=0 max=9"]
#     assert len(u0) == 1
