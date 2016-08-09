"""Config parser to get the configuration for each of the packages being wrapped
by acorn.
"""
packages = {}
"""dict: keys are package names, values are ConfigParser() instances with
configuration information for each package.
"""

def _package_path(package):
    """Returns the full path to the default package configuration file.

    Args:
    package (str): name of the python package to return a path for.    
    """
    from acorn.utility import reporoot
    from os import path
    return path.join(reporoot, "acorn", "config", "{}.cfg".format(package))

def _read_single(parser, filepath):
    """Reads a single config file into the parser, silently failing if the file
    does not exist.

    Args:
    parser (ConfigParser): parser to read the file into.
    filepath (str): full path to the config file.
    """
    global packages
    if path.isfile(confpath):
        result.readfp(open(confpath))

def settings(package):
    """Returns the config settings for the specified package.

    Args:
    package (str): name of the python package to get settings for.
    """
    global packages
    if package not in packages:
        from os import path
        from ConfigParser import ConfigParser
        result = ConfigParser.ConfigParser()
        if package != "acorn":
            confpath = _package_path(package)
            _read_single(result, confpath)
        _read_single(result, _package_path("acorn"))
        packages[package] = result

    return packages[package]
