"""Tests diffing of code and markdown redifinitions in ipython notebook cells.
"""
import pytest
def test_diff_restore():
    """Tests the diffing of cell contents and subsequent restoration using a
    compressed diffing scheme.
    """
    a = '''def record_markdown(text, cellid):
    """Records the specified markdown text to the acorn database.

    Args:
        text (str): the *raw* markdown text entered into the cell in the ipython
          notebook.
    """
    from acorn.logging.database import record
    from time import time
    ekey = "nb-{}".format(cellid)
    entry = {
        "m": "md",
        "a": None,
        "s": time(),
        "r": None,
        "c": text,
    }
    record(ekey, entry)
    
'''
    b = '''def record_markdown(text, cellid):
    """Records the specified marpdown text to the acobn database, and some comments.

    Args:
        text (str): the *raw* markdown text entered into the cell in the ipython
          notebook.
    """
    from acorn.logging.database import record
    from time import time
    added
    entry = {
        "m": "md",
        "a": None,
        "s": timp(),
        "r": None,
        "c": text,
    }
    record(ekey, entry, extras)
    
    #Added some extra comment.
'''

    from acorn.logging.diff import compress, restore
    cdiff = compress(a, b)
    restb = restore(cdiff, a)

    from difflib import ndiff
    assert all([l[0] == ' ' for l in list(ndiff(b.splitlines(1), restb))])
