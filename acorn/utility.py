"""Utility functions needed globally by all the sub-packages.
"""
def _get_reporoot():
    """Returns the absolute path to the repo root directory on the current
    system.
    """
    from os import path
    import acorn
    medpath = path.abspath(acorn.__file__)
    return path.dirname(path.dirname(medpath))

def abspath(fpath):
    """Returns the absolute path to the specified file/folder *relative to the
    repository root*.

    Args:
        fpath (str): path to a file or folder; doesn't need to exist.
    """
    from os import path, getcwd, chdir
    original = getcwd()
    chdir(reporoot)
    result = path.abspath(path.expanduser(fpath))
    chdir(original)
    return result
    
reporoot = _get_reporoot()
"""The absolute path to the repo root on the local machine.
"""

