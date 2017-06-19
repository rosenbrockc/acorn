"""Tests the acorn script access that configures settings and launches the
frontend notebook django server.
"""
import pytest
def get_sargs(args):
    """Returns the list of arguments parsed from sys.argv.
    """
    import sys
    sys.argv = args
    from acorn.acrn import _parser_options
    return _parser_options()    

def test_examples():
    """Makes sure the script examples work properly.
    """
    argv = ["py.test", "-examples"]
    from acorn.acrn import run
    args = get_sargs(argv)
    assert run(args) is None

def test_config():
    """Tests establishment of the local configuration directory.
    """
    from acorn.acrn import run
    argv = ["py.test", "configure", "packages"]
    args = get_sargs(argv)    
    assert run(args) is None

    #Trigger a warning since we don't have such a sub-command.
    argv = ["py.test", "configure", "dummy"]
    args = get_sargs(argv)    
    assert run(args) is None
    
