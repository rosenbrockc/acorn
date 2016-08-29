"""Methods for dynamically adding decorators to all the methods and
classes within a module. Uses some code from
https://github.com/clarete/forbiddenfruit to handle the c-complied extension
modules that are common in optimized codes.
"""
from acorn import msg
from database import tracker, record
from time import time
from analysis import analyze
def isbound(method):
    """Returns True if the method is bounded (i.e., does *not* require a
    class instance to run.)
    """
    if hasattr(method, "__acorn__") and method.__acorn__ is not None:
        return method.__acorn__.im_self
    elif hasattr(method, "im_self"):
        return method.im_self is not None
    else:
        return False

name_filters = {}
"""dict: keys are package names; values are dicts of lists: 1)
:meth:`~fnmatch.fnmatch` patterns; 2) :meth:`re.match` patterns.
"""
def _get_name_filter(package, context="decorate", reparse=False):
    """Makes sure that the name filters for the specified package have been
    loaded.

    Args:
        package (str): name of the package that this method belongs to.
        context (str): one of ['decorate', 'time', 'analyze']; specifies which
          section of the configuration settings to check.
    """
    global name_filters
    pkey = (package, context)
    if pkey in name_filters and not reparse:
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
                    filters.extend(re.split(r"\s*\$\s*", spack.get(section, "filter")))
                if "rfilter" in options:
                    pfilters = re.split(r"\s*\$\s*", spack.get(section, "rfilter"))
                    rfilters.extend([re.compile(p, re.I) for p in pfilters])
                if "ignore" in options:
                    ignores.extend(re.split(r"\s*\$\s*", spack.get(section, "ignore")))
                if "rignore" in options:
                    pignores = re.split(r"\s*\$\s*", spack.get(section, "rignore"))
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
    matched = True
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

def _tracker_str(item):
    """Returns a string representation of the tracker object for the given item.
    
    Args:
        item: object to get tracker for.
        fqdn (str): fully-qualified domain name of the object.
    """
    instance = tracker(item)
    if instance is not None:
        if isinstance(instance, str):
            return instance
        else:
            return instance.uuid
    else:
        return str(item)
    
def _check_args(*argl, **argd):
    """Checks the specified argument lists for objects that are trackable.
    """
    args = {"__": []}
    for item in argl:
        args["__"].append(_tracker_str(item))
           
    for key, item in argd.items():
        args[key] = _tracker_str(item)
        
    return args

def _reduced_stack(package):
    """Returns the reduced function call stack that includes only relevant
    function calls (i.e., ignores any that are not part of the specified package
    or acorn.

    Args:
        package (str): name of the package that the logged method belongs to.
    """
    import inspect
    #TODO: we need to update the second or statement that pulls out
    #acorn-specific files once we have it installed in an env.
    return [i[3] for i in inspect.stack()
            if package in i[1] or "decoration" in i[1]]

_atdepth_new = False
"""bool: when True, a higher-level creation method has already determined that
the stack is as deep is it needs to be; this allows subsequent method calls to
exit more quickly without examining the stack.
"""
_cstack_new = []
"""list: as constructors call ever more instance constructors, we place them on
this list and pop them once they return; that way, we know when to reset the
global at-depth flag.
"""

def creationlog(base, package, stackdepth=2):
    """Decorator for wrapping the creation of class instances that are being logged
    by acorn.

    Args:
        base: base class used to call __new__ for the construction.
        package (str): name of (global) package the class belongs to.
        stackdepth (int): if the calling stack is less than this depth, than
          include the entry in the log; otherwise ignore it.
    """   
    @staticmethod
    def wrapnew(cls, *argl, **argd):
        global _atdepth_new, _cstack_new
        if not _atdepth_new:
            reduced = len(_reduced_stack(package))
        else:
            reduced = stackdepth + 10
            
        #We are only interested in tracking constructors when the stack is
        #1-deep.
        if reduced <= stackdepth:
            args = _check_args(*argl, **argd)
            ekey = _tracker_str(cls)
            entry = {
                "method": "{}.__new__".format(cls.__name__),
                "args": args,
                "start": time(),
                "returns": None
                }
        else:
            _atdepth_new = True

        try:
            _cstack_new.append(cls)
            result = base.__old__(cls, *argl, **argd)
        except TypeError:
            #This is a crazy hack! We want this to be dynamic so that it can
            #work with any of the packages. If the error message suggests using
            #a different constructor, we go ahead and use it.
            import sys
            xcls, xerr = sys.exc_info()[0:2]
            referral = xerr.args[0].split()[-1]
            if ".__new__()" in referral:
                t = eval(referral.split('.')[0])
                result = t.__new__(cls, *argl, **argd)

        base.__init__(result, *argl, **argd)

        #Unfortunately, we also need to override the new instance's methods so
        #that they function correctly.
        from inspect import ismethod
        for n, o in vars(result).items():
            if ismethod(o) and not isbound(o):
                o.__call__ = getattr(cls, n)
        
        if reduced <= stackdepth:
            if result is not None:
                #We need to get these results a UUID that will be saved so that any
                #instance methods applied to this object has a parent to refer to.
                retid = _tracker_str(result)
                entry["returns"] = retid
            msg.info(entry, 2)
            record(ekey, entry)
            
        _cstack_new.pop()
        if len(_cstack_new) == 0:
            _atdepth_new = False
                        
        return result
    return wrapnew

_atdepth_call = False
"""bool: when True, a higher-level calling method has already determined that
the stack is as deep is it needs to be; this allows subsequent method calls to
exit more quickly without examining the stack.
"""
_cstack_call = []
"""list: as methods call ever more instance constructors, we place them on
this list and pop them once they return; that way, we know when to reset the
global at-depth flag.
"""

def callinglog(func, fqdn, package, stackdepth=2):
    """Decorator for wrapping package library methods for intelligent
    logging.
    
    Args:
        fqdn (str): fully qualified name of the method being decorated.
        package (str): name of the package the `func` belongs to.
        stackdepth (int): if the calling stack is less than this depth, than
          include the entry in the log; otherwise ignore it.
    """
    def wrapper(*argl, **argd):
        global _atdepth_call, _cstack_call
        if not _atdepth_call:
            rstack = _reduced_stack(package)
            reduced = len(rstack)
            msg.info("stack ({}): {}".format(len(rstack), ', '.join(rstack)), 3)
        else:
            reduced = stackdepth + 10
            
        if reduced <= stackdepth:
            args = _check_args(*argl, **argd)

            # At this point, we should start the entry. If the method raises an
            # exception, we should keep track of that. If this is an instance
            # method, we should get its UUID, if not, then we can just store the
            # entry under the full method name.
            if isbound(func):
                ekey = fqdn
            else:
                # It must have the first argument be the instance.
                ekey = _tracker_str(argl[0])

            name = fqdn.split('.')[-1]
            entry = {
                "method": name,
                "args": args,
                "start": time(),
                "returns": None
                }
        else:
            _atdepth_call = True
                
        # We time the actual method call. For ML fits, this is super important
        # because it adds perspective when choosing an optimal model.
        try:
            _cstack_call.append(fqdn)
            result = func(*argl, **argd)
        except:
            import sys
            if reduced <= stackdepth:
                xcls, xerr = sys.exc_info()[0:2]
                import traceback
                traceback.print_tb(sys.exc_info()[2])
                entry["error"] = "{}{}".format(xcls.__name__, xerr.args)
            result = None

        if reduced <= stackdepth:
            if result is not None:
                retid = _tracker_str(result)
                entry["returns"] = retid

            if filter_name(name, package, "time"):
                entry["elapsed"] = time() - entry["start"]
            if filter_name(name, package, "analyze"):
                entry["analysis"] = analyze(fqdn, result)

            msg.info(entry, 2)
            # Before we return the result, let's first save this call to the
            # database so we have a record of it.
            record(ekey, entry)

        _cstack_call.pop()
        if len(_cstack_call) == 0:
            _atdepth_call = False
            
        return result

    return wrapper

_extended_objs = {}
"""dict: keys are :func:`id` memory addresses of objects; values are the
*extended* objects that `acorn` created.
"""
_final_objs = []
"""list: of :func:`id` memory addresses of objects; these are objects marked as
final that cannot be subclassed and also cannot have their attributes set.
"""
def _create_extension(o, otype):
    """Creates an extension object to represent `o` that can have attributes
    set, but which behaves identically to the given object.

    Args:
        o: object to create an extension for; no checks are performed to see if
          extension is actually required.
        otype (str): object types; one of ["classes", "functions", "methods",
          "modules"].
    """
    xdict = {"__acornext__": o,
             "__doc__": o.__doc__}
    if otype == "classes":
        classname = o.__name__
        try:
            xclass = type(classname, (o, ), xdict)
            xclass.__module__ = o.__module__
            return xclass
        except TypeError:
            #This happens when a class is final, meaning that it is not allowed
            #to be subclassed.
            _final_objs.append(id(o))
            return o
    elif otype in ["functions"]:
        def xwrapper(*args, **kwargs):
            o(*args, **kwargs)
        xwrapper.__dict__.update(xdict)
        for a, v in o.__dict__.items():
            #We want the new function to be identical to the old except that
            #it's __call__ method, which we overrode above.
            if a != "__call__":
                setattr(xwrapper, a, v)
        return xwrapper

_set_failures = []
"""list: of :meth:`id` integer memory address values of those objects that
cannot be handled in a safe way to have their attributes set without resorting
to forbidden fruit.
"""
def _safe_setattr(obj, name, value):
    """Safely sets the attribute of the specified object. This includes not
    setting attributes for final objects and setting __func__ for instancemethod
    typed objects.

    Args:
        obj: object to set an attribute for.
        name (str): new attribute name.
        value: new attribute value.

    Returns:
        bool: True if the set attribute was successful.
    """
    okey = id(obj)
    if okey in _set_failures or okey in _final_objs:
        return False
    
    import inspect
    try:
        if inspect.ismethod(obj):
            setattr(obj.__func__, name, value)
            return True
        else:
            setattr(obj, name, value)
            return True
    except TypeError:
        _set_failures.append(okey)
        msg.warn("Failed '{}' attribute set on {}.".format(name, obj))
        return False
    
def _extend_object(parent, n, o, otype):
    """Extends the specified object if it needs to be extended. The method
    attempts to add an attribute to the object; if it fails, a new object is
    created that inherits all of `o` attributes, but is now a regular object
    that can have attributes set.

    Args:
        parent: has `n` in its `__dict__` attribute.
        n (str): object name attribute.
        o (list): object instances to be extended.
        otype (str): object types; one of ["classes", "functions", "methods",
          "modules"].
    """
    try:
        #The __acornext__ attribute references the original, unextended
        #object; if the object didn't need extended, then __acornext__ is
        #none.
        if otype == "methods":
            setattr(o.__func__, "__acornext__", None)
        else:
            setattr(o, "__acornext__", None)
        fqdn = _fqdn(o, otype)
        return o
    except TypeError:
        #We have a built-in or extension type. 
        okey = id(o)
        if okey not in _extended_objs:
            #We need to generate an extension for this object and store it
            #in the extensions dict.
            xobj = _create_extension(o, otype)
            fqdn = _fqdn(xobj, otype)
            if xobj is not None:
                _extended_objs[okey] = xobj
            #else: we can't handle this kind of object; it just won't be
            #logged...
        setattr(parent, n, _extended_objs[okey])
        return _extended_objs[okey]

def _split_object(pobj, package):
    """Splits the specified object into its modules, classes, methods and
    functions so that it can be decorated more easily. For extension
    modules/classes that can't have attributes set, the object's dictionary is
    modified to point to a derived-type version.

    Args:
        pobj: object instance returned from the import.
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
    
    prepack = "{}.".format(package)
    pms = []
    for n, o in vars(pobj).items():
        omod = inspect.getmodule(o)
        if omod is not None and prepack in omod.__name__:
            pms.append((n, o))
            
    for n, o in pms:
        for t, f in tests.items():
            if f(o):
                xobj = _extend_object(pobj, n, o, t)
                result[t].append((n, xobj))

    return result

def _fqdn(o, otype):
    """Returns the fully qualified name of the object.

    Args:
        o (type): instance of the object's type.
        otype (str): one of ['classes', 'functions', 'methods', 'modules'];
          specifies which group the object belongs to.
    """
    if id(o) in _set_failures:
        return None
    
    if not hasattr(o, "__fqdn__"):
        import inspect
        if not hasattr(o, "__name__"):
            msg.warn("Object {} has no __name__ attribute. Skipping.".format(o))
            return
        
        result = None
        result = "{}.{}".format(inspect.getmodule(o).__name__, o.__name__)
        # if otype in ["classes", "functions"]:
        #     result = "{}.{}".format(o.__module__, o.__name__)
        # elif otype == "methods":
        #     if isbound(o):
        #         result = "{}.{}".format(_fqdn(o.im_self, "classes"), o.__name__)
        #     else:
        #         result = "{}.{}".format(_fqdn(o.im_class, "classes"), o.__name__)
        # elif otype == "modules":
        #     result = o.__name__

        _safe_setattr(o, "__fqdn__", result)

    if hasattr(o, "__fqdn__"):
        return o.__fqdn__

_stack_config = {}
"""dict: keys are package names, values are :type:`dict` where the keys are
fqdns of package members and values are the configured stack depths.
"""
def _get_stack_depth(package, fqdn, defdepth=2):
    """Loads the stack depth settings from the config file for the specified
    package.

    Args:
        package (str): name of the package to get stack depth info for.
        fqdn (str): fully qualified domain name of the member in the package.
        defdepth (int): default depth when one has not been configured.
    """
    global _stack_config
    if package not in _stack_config:
        from acorn.config import settings
        spack = settings(package)
        if spack is None:
            _stack_config[package] = None
            return None
        else:
            _stack_config[package] = {}

        secname = "logging.depth"
        if spack.has_section(secname):
            for ofqdn in spack.options(secname):
                _stack_config[package][ofqdn] = spack.getint(secname, ofqdn)

    if fqdn in _stack_config[package]:
        return _stack_config[package][fqdn]
    elif "*" in _stack_config[package]:
        return _stack_config[package]["*"]
    else:
        return defdepth

_decor_count = {}
"""dict: keys are package names, values are list [decorated, skipped, na] that
keeps statistics on how many of the package objects actually get decorated.
"""
    
def _decorate_obj(parent, n, o, otype, recurse=True, redecorate=False):
    """Adds the decoration for automated logging to the specified object, if it
    hasn't already been done.

    Args:
        parent: object that `o` belongs to.
        n (str): name in the parent's dictionary.
        o (type): instance of the object's type.
        otype (str): one of ['classes', 'functions', 'methods', 'modules'];
          specifies which group the object belongs to.
        recurse (bool): when True, the objects methods and functions are also
          decorated recursively.
    """
    global _decor_count
    if not hasattr(o, "__acorn__") or redecorate:
        fqdn = _fqdn(o, otype)
        if fqdn is None:
            #This object didn't have a name, which means we can't extend it or
            #track it anyway.
            return
        
        package = fqdn.split('.')[0]
        if filter_name(n, package) and filter_name(fqdn, package):
            d = _get_stack_depth(package, fqdn)
            if hasattr(o, "__call__") and otype != "classes":
                #calling on class types is handled by the construction decorator
                #below.
                _safe_setattr(o, "__acorn__", o.__call__)
                setok = _safe_setattr(parent, n,
                                      callinglog(o.__call__, fqdn, package, d))
                msg.okay("Set calling logger on {}: {}.".format(n, fqdn), 3)
                _decor_count[package][0] += 1
            else:
                setok = _safe_setattr(o, "__acorn__", None)
                _decor_count[package][2] += 1

            if otype == "classes" and setok:
                if hasattr(o, "__new__"):
                    setattr(o, "__old__", staticmethod(o.__new__))
                    setattr(o, "__new__", creationlog(o, package, d))
                    msg.gen("Set creation logger on {}: {}.".format(n, fqdn),3)
                    _decor_count[package][0] += 1
                #else: must have only static methods and no instances.
                
            #We don't need to bother recursing for those modules/classes that
            #can't have their attributes set, since their members will have the
            #same restrictions.
            if setok and otype in ["classes", "modules"]:
                #These types can be further decorated; let's traverse their members
                #and try to decorate those as well.
                splits = _split_object(o, package)
                for ot, ol in splits.items():
                    for nobj, obj in ol:
                        _decorate_obj(o, nobj, obj, ot)
        else:
            skipmsg = "Skipping {}: {} because of filter rules."
            msg.info(skipmsg.format(n, fqdn), 4)
            _decor_count[package][1] += 1
    
def decorate(package):
    """Decorates all the methods in the specified package to have logging
    enabled according to the configuration for the package.
    """
    global _decor_count
    _decor_count[package.__name__] = [0, 0, 0]
    packsplit = _split_object(package, package.__name__)
    for ot, ol in packsplit.items():
        for name, obj in ol:
            _decorate_obj(package, name, obj, ot)
    msg.info("Decorated/Skipped/NA = {}".format(_decor_count))
