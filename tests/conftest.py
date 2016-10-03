"""Exposes a session-available temporary directory for the acorn database files
generated during unit testing.
"""
import pytest
from acorn.base import set_testmode
set_testmode(True)

#Because of the way coverage testing works, acorn gets imported *before* this
#session-level initialization. That means the local user copy of the config will
#be referenced instead of the repo's version for the unit tests. We re-import
#the acorn configuration here to undo that.
from acorn.config import settings
settings("acorn", True)

@pytest.fixture(scope='session', autouse=True)
def dbdir(tmpdir_factory):
    fn = tmpdir_factory.mktemp('dbs')
    return fn
