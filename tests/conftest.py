"""Exposes a session-available temporary directory for the acorn database files
generated during unit testing.
"""
import pytest
@pytest.fixture(scope='session', autouse=True)
def dbdir(tmpdir_factory):
    from acorn.base import set_testmode
    set_testmode(True)
    fn = tmpdir_factory.mktemp('dbs')
    return fn
