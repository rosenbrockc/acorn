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

reporoot = _get_reporoot()
"""The absolute path to the repo root on the local machine.
"""

