"""Tests the decoration and logging of the sklearn package by running some
common code lines and checking that the logged entries make sense. Also, checks
the analysis functions for the fit and predict methods to make sure they are
working.
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
    return db_init("sklearn", dbdir)

def test_decorate():
    """Tests the decoration of the full numpy module. Since the module can
    change, the exact number of methods and objects decorated will be constantly
    changing. Instead, we just make sure that some were decorated, skipped and
    N/A in the module statistics.
    """
    import acorn.sklearn as skl
    from db import decorate_check
    decorate_check("sklearn")

    from acorn.analyze.sklearn import set_auto_print, set_auto_predict
    set_auto_predict(True)
    set_auto_print(True)

def test_classify():
    """Tests classification using several common classifiers; also tests
    :func:`sklearn.datasets.make_classification`.
    """
    from sklearn.datasets import make_classification
    kwds = {'n_clusters_per_class': 1, 'n_informative': 2,
            'random_state': 1, 'n_features': 2, 'n_redundant': 0}
    X, y = make_classification(**kwds)

    import acorn.numpy as np
    rng = np.random.RandomState(2)
    X += 2 * rng.uniform(size=X.shape)

    from sklearn.preprocessing import StandardScaler
    from sklearn.cross_validation import train_test_split
    X = StandardScaler().fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.4)
    
    from sklearn.svm import SVC
    svc = SVC()
    svc.fit(X_train, y_train)

    yL=svc.predict(X_test)

    from db import db_entries
    sentries, uuids = db_entries("sklearn")
    
    #Unfortunately, py2 and py3 are getting different stack lengths on the
    #calls, so we have to handle them (almost) separately. Since this is the
    #first test in the module, we don't have to look backwards. Just take the
    #entries as they are
    ue = sentries
    u0, e0 = sentries[0] #make classification
    u1, e1 = sentries[1] #RandomState constructor
    #There are two calls to random seed; skip one of them.
    us, es = sentries[3] #Random seed (sub-call of u1)
    usu, esu = sentries[4] #Random.uniform instance method call.
    u2, e2 = sentries[5] #multiply by 2
    u3, e3 = sentries[6] #iadd on X
    u4, e4 = sentries[7] #Standard scaler constructor.
    #There are also two calls to standard scaler constructor. Ignore the second.
    u5, e5 = sentries[9] #Standard scaler fit_transform.
    u6, e6 = sentries[10] #train_test_split

    if len(sentries) == 14:
        ui = 11
    else:
        print(len(sentries))
        ui = 12
    u7, e7 = sentries[ui] #SVC constructor
    u8, e8 = sentries[ui+1] #SVC fit
    u9, e9 = sentries[ui+2] #SVC predict

    assert e0["m"] == "sklearn.datasets.samples_generator.make_classification"
    assert e0["a"]["_"] == []
    for kw, val in kwds.items():
        assert kw in e0["a"]
        assert e0["a"][kw] == val
    assert len(u0) == 2

    if six.PY3:
        randclass = "numpy.random.mtrand"
    else:
        randclass = "numpy.random"
        
    assert e1["m"] == "{}.RandomState.__new__".format(randclass)
    assert e1["a"]["_"] == [2]
    assert e1["r"] == u1

    assert es["m"] == "numpy.random.mtrand.RandomState.seed"
    assert es["a"]["_"] == [u1, 2]
        
    assert esu["m"] == "numpy.random.mtrand.RandomState.uniform"
    assert esu["a"]["_"] == [u1]
    assert "'tuple'> len=2 min=2 max=100" in esu["a"]["size"]
    usr = esu["r"]

    assert e2["m"] == "numpy.ufunc.multiply"
    assert e2["a"]["_"] == [2, usr]

    assert e3["m"] == "numpy.ufunc.add"
    assert e3["a"]["_"] == [u0[0], u2, u0[0]]
    
    assert e4["m"] == "sklearn.preprocessing.data.StandardScaler.__new__"
    assert e4["r"] == u4
    
    assert e5["m"] == "sklearn.base.fit_transform"
    assert e5["a"]["_"] == [u4, u3]
    #fit_transform was an instance method on the standard scaler, so the actual
    #transformed matrix will show up in the return value.
    uft = e5["r"]

    assert e6["m"] == "sklearn.cross_validation.train_test_split"
    assert e6["a"]["_"] == [uft, u0[1]]
    
    assert e7["m"] == "sklearn.svm.classes.SVC.__new__"
    assert e7["r"] == u7

    assert e8["m"] == "sklearn.svm.base.fit"
    assert e8["a"]["_"] == [u7, u6[0], u6[2]]
    assert '%' in e8["z"]
    assert e8["z"]['%'] > 0
    assert "e" in e8
    assert isinstance(e8["e"], float)
    
    assert e9["m"] == "sklearn.svm.base.predict"
    assert e9["a"]["_"] == [u7, u6[1]]
    assert '%' in e9["z"]
    assert e9["z"]['%'] > 0
