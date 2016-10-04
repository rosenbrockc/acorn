"""Config parser to get the configuration for each of the packages being wrapped
by acorn.
"""
packages = {}
"""dict: keys are package names, values are ConfigParser() instances with
configuration information for each package.
"""
from six.moves.configparser import ConfigParser
class CaseConfigParser(ConfigParser):
    """Case-sensitive configuration parser; we need to preseve the
    case-sensitive names of FQDNs in the option strings.
    """
    def optionxform(self, optionstr):
        return optionstr
    
def config_dir(mkcustom=False):
    """Returns the configuration directory for custom package settings.
    """
    from acorn.utility import reporoot
    from acorn.base import testmode
    from os import path
    alternate = path.join(path.abspath(path.expanduser("~")), ".acorn")
    if testmode or (not path.isdir(alternate) and not mkcustom):
        return path.join(reporoot, "acorn", "config")
    else:
        if mkcustom:
            from os import mkdir
            mkdir(alternate)
        return alternate

def _package_path(package):
    """Returns the full path to the default package configuration file.

    Args:
    package (str): name of the python package to return a path for.    
    """
    from os import path
    confdir = config_dir()
    return path.join(confdir, "{}.cfg".format(package))

def _read_single(parser, filepath):
    """Reads a single config file into the parser, silently failing if the file
    does not exist.

    Args:
    parser (ConfigParser): parser to read the file into.
    filepath (str): full path to the config file.
    """
    from os import path
    global packages
    if path.isfile(filepath):
        parser.readfp(open(filepath))

def settings(package, reload_=False):
    """Returns the config settings for the specified package.

    Args:
        package (str): name of the python package to get settings for.
    """
    global packages
    if package not in packages or reload_:
        from os import path
        result = CaseConfigParser()
        if package != "acorn":
            confpath = _package_path(package)
            _read_single(result, confpath)
        _read_single(result, _package_path("acorn"))
        packages[package] = result

    return packages[package]

def _descriptor_path(package):
    """Returns the full path to the default package configuration file.

    Args:
    package (str): name of the python package to return a path for.    
    """
    from os import path
    return path.join(config_dir(), "{}.json".format(package))

def descriptors(package):
    """Returns a dictionary of descriptors deserialized from JSON for the
    specified package.

    Args:
        package (str): name of the python package to get settings for.
    """
    from os import path
    dpath = _descriptor_path(package)
    if path.isfile(dpath):
        import json
        with open(dpath) as f:
            jdb = json.load(f)
        return jdb
    else:
        return None
