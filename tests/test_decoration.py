"""Tests the extras in the decoration module that are never called during normal
use.
"""
import six
def test_iswhat():
    """Tests the iswhat tester for an object.
    """
    from acorn.logging.decoration import iswhat
    import numpy as np
    rs = iswhat(np.random.RandomState)
    assert rs["isbuiltin"] == False
    assert rs["isclass"] == True
    if six.PY2:
        assert len(rs) == 16
    else:
        assert len(rs) == 19
    

    un = iswhat(np.random.RandomState.uniform)
    assert un["isroutine"] == True
    if six.PY2:
        assert un["isfunction"] == False
    else:
        assert un["isfunction"] == True
    assert un["ismethoddescriptor"] == False

def test_namefilters():
    """Tests behavior for bogus package names and contexts.
    """
    from acorn.logging.decoration import _get_name_filter, filter_name
    assert _get_name_filter("sklearn", "bogus") is None
    assert filter_name("unnecessary", "sklearn", "bogus") == True
