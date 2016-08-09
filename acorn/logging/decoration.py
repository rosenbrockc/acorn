"""Methods for dynamically adding decorators to all the methods and
classes within a module.
"""
from database import tracker, record
from time import time
from analysis import analyze
def isbound(method):
    """Returns True if the method is bounded (i.e., does not require a
    class instance to run.
    """
    return method.im_self is not None

name_filters = {}
"""dict: keys are package names; values are dicts of lists: 1)
:meth:`~fnmatch.fnmatch` patterns; 2) :meth:`re.match` patterns.
"""
def _get_name_filter(package, context="decorate"):
    """Makes sure that the name filters for the specified package have been
    loaded.

    Args:
        package (str): name of the package that this method belongs to.
        context (str): one of ['decorate', 'time', 'analyze']; specifies which
          section of the configuration settings to check.
    """
    global name_filters
    pkey = (package, reason)
    if pkey in name_filters:
        return name_filters[pkey]
    
    from acorn.config import settings
    spack = settings(package)
    if spack is None:
        name_filters[pkey] = None
        return None

    # The acorn.* sections allow for global settings that affect every package
    # that ever gets wrapped.
    sections = {
        "decorate": ["tracking", "acorn.tracking"],
        "time": ["timing", "acorn.timing"],
        "analyze": ["analysis", "acorn.analysis"]
        }

    filters, rfilters = None, None
    import re
    if context in sections:
        # We are interested in the 'filter' and 'rfilter' options if they exist.
        filters, rfilters = [], []
        ignores, rignores = [], []
        for section in sections[context]:
            if spack.has_section(section):
                options = spack.options(section)
                if "filter" in options:
                    filters.extend(re.split(r"\s*\$\s*", pack.get(section, "filter")))
                if "rfilter" in options:
                    pfilters = re.split(r"\s*\$\s*", pack.get(section, "rfilter"))
                    rfilters.extend([re.compile(p, re.I) for p in pfilters])
                if "ignore" in options:
                    ignores.extend(re.split(r"\s*\$\s*", pack.get(section, "filter")))
                if "rignore" in options:
                    pignores = re.split(r"\s*\$\s*", pack.get(section, "rfilter"))
                    rignores.extend([re.compile(p, re.I) for p in pfilters])

        name_filters[pkey] = {
            "filters": filters,
            "rfilters": rfilters,
            "ignores": ignores,
            "rignores": rignores
            }
    else:
        name_filters[pkey] = None
    return name_filters[pkey]

def filter_name(funcname, package, context="decorate"):
    """Returns True if the specified function should be filtered (i.e., included
    or excluded for use in the specified context.)

    Args: 
        funcname (str): name of the method/function being called.
        package (str): name of the package that the method belongs to.
        context (str): one of ['decorate', 'time', 'analyze']; specifies which
          section of the configuration settings to check.

    Returns:
    bool: specifying whether the function should be decorated, timed or
      analyzed.
    """
    packfilter = _get_name_filter(package, context)
    if packfilter is None:
        # By default, if there are no rules specified, then we include
        # everything.
        return True

    # First we handle the `fnmatch` filters. If something is told to be ignored,
    # that takes precedence over the inclusion filters.
    matched = False
    if packfilter["ignores"] is not None:
        from fnmatch import fnmatch
        for pattern in packfilter["ignores"]:
            if fnmatch(funcname, pattern):
                matched = False
                return matched

    if not matched and packfilter["rignores"] is not None:
        for pattern in packfilter["rignores"]:
            if pattern.match(funcname):
                matched = False
                return matched
                
    if packfilter["filters"] is not None:
        from fnmatch import fnmatch
        for pattern in packfilter["filters"]:
            if fnmatch(funcname, pattern):
                matched = True
                break

    if not matched and packfilter["rfilters"] is not None:
        for pattern in packfilter["rfilters"]:
            if pattern.match(funcname):
                matched = True
                break

    return matched

def _check_args(*argl, **argd):
    """Checks the specified argument lists for objects that are trackable.
    """
    args = {"__": []}
    for item in argl:
        instance = tracker(item)
        if instance is not None:
            args["__"].append(instance.uuid)
        else:
            args["__"].append(str(item))
            
    for key, item in argd.items():
        instance = tracker(item)
        if instance is not None:
            args[key].append(instance.uuid)
        else:
            args[key].append(str(item))
    return args

class LoggingDecorator(object):
    """Class instance for wrapping package library methods for intelligent
    logging.
    
    Args:
        fqdn (str): fully qualified name of the method being decorated.
    """
    def __init__(self, fqdn):
       self.package = fqdn.split(".")[0]
       self.fqdn = fqdn

    def __call__(self, func):
        def wrapper(*argl, **argd):
            args = _check_args(*argl, **argd)

            # At this point, we should start the entry. If the method raises an
            # exception, we should keep track of that. If this is an instance
            # method, we should get its UUID, if not, then we can just store the
            # entry under the full method name.
            if isbound(func):
                ekey = self.fqdn
            else:
                # It must have the first argument be the instance.
                ekey = tracker(argl[0]).uuid
            entry = {
                "method": func.func_name,
                "args": args,
                "start": time()
                }
                    
            # We time the actual method call. For ML fits, this is super important
            # because it adds perspective when choosing an optimal model.
            try:
                result = func(*argl, **argd)
            except:
                entry["error"] = sys.exc_info()[0]
                result = None
                
            if filter_name(func.func_name, self.package, "time"):
                entry["elapsed"] = time() - entry["start"]
            if filter_name(func.func_name, self.package, "analyze"):
                entry["analysis"] = analyze(self.fqdn, result)

            # Before we return the result, let's first save this call to the
            # database so we have a record of it.
            record(ekey, entry)
            return result

        return wrapper

def _split_package(pobj, package):
    """Splits the specified package into its modules, classes, methods and
    functions so that it can be decorated more easily.

    Args:
        pobj: package instance returned from the import.
        package (str): name of the package (used for filtering all the loaded
          packages and methods inside the package object).
    """
    import inspect
    result = {
        "classes": [],
        "functions": [],
        "methods": [],
        "modules": []
        }

    tests = {
        "classes": inspect.isclass,
        "functions": inspect.isfunction,
        "methods": inspect.ismethod,
        "modules": inspect.ismodule
        }
    
    pms = [(n, o) for (n, o) in inspect.getmembers(pobj) if package in str(o)]
    for n, o in pms:
        for t, f in tests:
            if f(o):
                result[t] = (n, o)

    return result

def _fqdn(n, o, otype):
    """Returns the fully qualified name of the object.

    Args:
    n (str): name of the object.
    o (type): instance of the object's type.
    otype (str): one of ['classes', 'functions', 'methods', 'modules'];
      specifies which group the object belongs to.
    """
    

import inspect
def _list_methods(entity):
    """Lists all the methods or functions within the specified entity.
    
    Args:
        entity (type): the type description of the module or class to grab
          methods and functions from.
    """
    methods = []
    for (n, f) in inspect.getmembers(entity):
        # We ignore all methods that start with "_" by default.
        if n[0] == '_':
            continue
        if inspect.ismethod(f) or inspect.isfunction(f):
            methods.append((n, f))
        elif inspect.isclass(f):
            methods.extend(_list_methods(f))
        elif inspect.ismodule(f):
            methods.extend(_list_methods(f))
        
    return methods

def decorate(package):
    """Decorates all the methods in the specified package to have logging
    enabled according to the configuration for the package.
    """
    pass
