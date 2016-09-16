"""Tests the decoration and logging of the sklearn package by running some
common code lines and checking that the logged entries make sense. Also, checks
the analysis functions for the fit and predict methods to make sure they are
working.
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
    return db_init("sklearn", tmpdir)

def test_decorate():
    """Tests the decoration of the full numpy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.sklearn as skl
    from db import decorate_check
    decorate_check("sklearn")

def test_classify():
    """Tests classification using several common classifiers; also tests
    :func:`sklearn.datasets.make_classification`.
    """
    from sklearn.datasets import make_moons, make_circles, make_classification
    X, y = make_classification(n_features=2, n_redundant=0, n_informative=2,
                               random_state=1, n_clusters_per_class=1)

    
