"""Class for altering the search paths within acorn for new/undecorated packages
(i.e., those that weren't checked explicitly when it was first designed.
"""
from acorn import msg
_packages = {}
"""dict: keys are package names; values are `bool` indicating whether `acorn`
should decorate the package with the loggers.
"""
_special = ["scipy", "sklearn", "matplotlib"]
"""list: of packages that have special extensions or import behavior and cannot
be deco-imported automatically by `acorn`.
"""
    
def _load_package_config(reload_=False):
    """Loads the package configurations from the global `acorn.cfg` file.
    """
    global _packages
    from acorn.config import settings
    packset = settings("acorn", reload_)
    if packset.has_section("acorn.packages"):
        for package, value in packset.items("acorn.packages"):
            _packages[package] = value.strip() == "1"

def reload_cache():
    """Reloads the configuration file settings for which packages to decorate.
    """
    global _packages
    _packages = {}
    _load_package_config(True)

hooks = []
"""list: of package names that have *already* been intercepted by our
loader/decorator. This allows us to skip them the next time they are imported
(by our scripts) so that we don't get into an infinite loop.
"""
    
import sys
class AcornMetaImportFinder(object):
    """Overrides the default `import` behavior of python for packages so that we
    can intercept and decorate certain packages, but not others.

    Args:
        prefix (str): prefix on import full names before they are considered
          loadable by acorn. Also available as an attribute.
    """
    def __init__(self, prefix="acorn"):
        self.prefix = prefix
    
    def find_module(self, fullname, packpath=None):
        global hooks
        if (fullname[0:len(self.prefix)] != self.prefix):
            return None

        if fullname.count('.') > 1:
            #Acorn isn't setup to work with sub-packages.
            return None

        already = False
        package = fullname.split('.')[-1]
        if package in _packages and _packages[package]:
            if package not in hooks:
                #We can import this one and decorate it using the default or
                #custom tools in acorn.
                hooks.append(package)
                msg.okay("Import override: '{}'.".format(package), 3)
                return AcornDecoratingLoader(package)
            else:
                already = True

        if not already:
            msg.info("Skipping import override: '{}'.".format(packpath), 3)

def load_decorate(package):
    """Imports and decorates the package with the specified name.
    """
    # We import the decoration logic from acorn and then overwrite the sys.module
    # for this package with the decorated, original pandas package.
    from acorn.logging.decoration import set_decorating, decorating
    
    #Before we do any imports, we need to set that we are decorating so that
    #everything works as if `acorn` wasn't even here.
    origdecor = decorating
    set_decorating(True)

    #If we try and import the module directly, we will get stuck in a loop; at
    #some point we must invoke the built-in module loader from python. We do
    #this by removing our sys.path hook.
    import sys    
    from importlib import import_module
    apack = import_module(package)    
    from acorn.logging.decoration import decorate
    decorate(apack)

    sys.modules["acorn.{}".format(package)] = apack

    #Set the decoration back to what it was.
    from acorn.logging.decoration import set_decorating
    set_decorating(origdecor)
    
    return apack

class AcornStandardLoader(object): # pragma: no cover
    #I am having issues with intercepting all loads. At the least, pytest won't
    #import properly, so I am disabling this for now.
    """Loads packages *without* decoration, but with the correct flags enabled
    so that if those packages imported acorn decorated ones, they don't run all
    the logging machinery during imports.
    """
    def __init__(self, package):
        self.package = package
        
    def load_module(self, fullname):
        from acorn.logging.decoration import set_decorating, decorating
        global hooks
        odecor = decorating
        set_decorating(True)

        from importlib import import_module
        mod = import_module(fullname, self.package)
        hooks.remove(fullname)
        
        set_decorating(odecor)
        return mod

class AcornDecoratingLoader(object):
    """Loads packages that need to be decorated for automatic logging by
    `acorn`.

    Args:
        package (str): name of the package being loaded.
    """
    def __init__(self, package):
        self.package = package
        
    def load_module(self, fullname):
        if fullname in sys.modules: # pragma: no cover.
            msg.info("Reusing existing import for '{}'".format(fullname), 3)
            mod = sys.modules[fullname]
        else:
            msg.info("Decorating import for '{}'".format(self.package), 3)
            #First we import the package, then the specified sub-module that
            #they asked for.
            if self.package in _special:
                from importlib import import_module
                mod = import_module(fullname)
            else:
                mod = load_decorate(self.package)

        return mod
    
_load_package_config()
sys.meta_path.insert(0, AcornMetaImportFinder())

#TODO: we still need to get a package manager going. When we import the modules,
#we should always use the original package items. sklearn dies when numpy has
#already been decorated because our subclass doesn't jive with the c-extension
#modules it uses. But it is okay if it can use the original numpy class. If we
#get our own special __getattr__ method for acorn, we could return the decorated
#versions and still have the other imports work correctly. We lose the ability
#for the user to import directly from the module later (they would always have
#to go through acorn). Or perhaps we could look at the value of the global
#`decorating` and then decide which of the objects to return in getattr.
