"""Methods for dynamically adding decorators to all the methods and
classes within a module. The entries created by the decorators have been
pre-compressed for clarity and file size. Thus the short key names mean the
following:

.. code-block:: ini

    m = method
    a = args
    r = returns
    s = start
    e = elapsed
    x = analysis
    c = code

Examples:

Decorate a new package using the acorn decorator machinery.

>>> from acorn.logging.decoration import decorate
>>> import package
>>> decorate(package)

The decorate routine replaces all the members of the package with decorated ones
and does this recursively until the whole package is decorated. We can also use
the automatic decoration machinery with `acorn`. Open the `acorn.cfg` file and
add the name of the package to `[acorn.packages]`:

.. code-block:: ini

    package=1

Then, you can auto-decorate the package using:

.. code-block:: python

    import acorn.package
"""
from acorn import msg
from acorn.logging.database import tracker, record
from time import time
from acorn.logging.analysis import analyze
import acorn
import six
import inspect
from acorn.base import testmode

decorating = False
"""bool: when True, the script is decorating objects; if any other objects have
methods that call decorated objects, we don't want the decorations to log
entries since we are still in the initialization phase.
"""
streamlining = False
"""bool: when True, a method has disabled all logging for subsequent calls. The
method will reset this variable once it has executed. This is needed to optimize
packages like `matplotlib` that make thousands of calls for a high-level method
like plot.
"""

def iswhat(o):
    """Returns a dictionary of all possible identity checks available to
    :mod:`inspect` applied to `o`.

    Returns:
        dict: keys are `inspect.is*` function names; values are `bool` results
          returned by each of the methods.
    """
    import inspect
    isfs = {n: f for n, f in inspect.getmembers(inspect) if n[0:2] == "is"}
    return {n: f(o) for n, f in isfs.items()}

def _safe_getmodule(o):
    """Attempts to return the module in which `o` is defined.
    """
    from inspect import getmodule
    try:
        return getmodule(o)
    except: # pragma: no cover
        #There is nothing we can do about this for now.
        msg.err("_safe_getmodule: {}".format(o), 2)
        pass

def _safe_getattr(o):
    """Gets the attribute from the specified object, taking the acorn decoration
    into account.
    """
    def getattribute(attr): # pragma: no cover
        if hasattr(o, "__acornext__") and o.__acornext__ is not None:
            return o.__acornext__.__getattribute__(attr)
        elif hasattr(o, "__acorn__") and o.__acorn__ is not None:
            #Some of the functions have the original function (when it was not
            #extended) in the __acorn__ attribute.
            return o.__acorn__.__getattribute__(attr)
        else:
            return getattr(o, attr)
    return getattribute

def _safe_hasattr(o, attr):
    """Returns True if `o` has the specified attribute. Takes edge cases into
    account where packages didn't intend to be used like acorn uses them.
    """
    try:
        has = hasattr(o, attr)
    except: # pragma: no cover
        has = False
        msg.err("_safe_hasattr: {}.{}".format(o, attr), 2)
        pass
    return has

def _update_attrs(nobj, oobj, exceptions=None, acornext=False):
    """Updates the attributes on `nobj` to match those of old, excluding the any
    attributes in the exceptions list.
    """
    success = True
    if (acornext and hasattr(oobj, "__acornext__")
        and oobj.__acornext__ is not None): # pragma: no cover
        target = oobj.__acornext__
    else:
        target = oobj
        
    for a, v in _get_members(target):
        if hasattr(nobj, a):
            #We don't want to overwrite something that acorn has already done.
            continue
        if a in ["__class__", "__code__", "__closure__"]:# pragma: no cover
            #These attributes are not writeable by design.
            continue
        
        if exceptions is None or a not in exceptions:
            try:
                setattr(nobj, a, v)
            except TypeError:# pragma: no cover
                #Some of the built-in types have __class__ attributes (for
                #example) that we can't set on a function type. This catches
                #that case and any others.
                emsg = "_update_attrs (type): {}.{} => {}"
                msg.err(emsg.format(nobj, a, target), 2)
                pass
            except AttributeError:# pragma: no cover
                #Probably a read-only attribute that we are trying to set. Just
                #ignore it.
                emsg = "_update_attrs (attr): {}.{} => {}"
                msg.err(emsg.format(nobj, a, target), 2)
                pass
            except ValueError:# pragma: no cover
                emsg = "_update_attrs (value): {}.{} => {}"
                msg.err(emsg.format(nobj, a, target), 2)
                success = False

    return success

name_filters = {}
"""dict: keys are package names; values are dicts of lists. 1)
:meth:`~fnmatch.fnmatch` patterns; 2) :meth:`re.match` patterns.
"""
_decorated_packs = []
"""list: of package names that have had :func:`decorate` called on them.
"""
_pack_paths = ["<ipython-input", "matplotlib", "numpy", "scipy"]
"""list: of package name paths (including the path separator) so that stack
entries can be filtered more quickly.
"""
_def_stackdepth = 4
"""int: default stack depth when not specified by a config file.
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
                if "rfilter" in options: # pragma: no cover
                    #Until now, the fnmatch filters have been the most
                    #useful. So I don't have any unit tests for regex filters.
                    pfilters = re.split(r"\s*\$\s*", spack.get(section, "rfilter"))
                    rfilters.extend([re.compile(p, re.I) for p in pfilters])
                if "ignore" in options:
                    ignores.extend(re.split(r"\s*\$\s*", spack.get(section, "ignore")))
                if "rignore" in options: # pragma: no cover
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

def filter_name(funcname, package, context="decorate", explicit=False):
    """Returns True if the specified function should be filtered (i.e., included
    or excluded for use in the specified context.)

    Args: 
        funcname (str): name of the method/function being called.
        package (str): name of the package that the method belongs to.
        context (str): one of ['decorate', 'time', 'analyze']; specifies which
          section of the configuration settings to check.
        explicit (bool): when True, if a name is not explicitly specified for
          inclusion, then the function returns False.

    Returns:
        bool: specifying whether the function should be decorated, timed or
          analyzed.
    """
    packfilter = _get_name_filter(package, context)
    if packfilter is None:
        # By default, if there are no rules specified, then we include
        # everything.
        return True

    # First we handle the `fnmatch` filters. If something is explicitly included
    # that takes precedence over the ignore filters.
    matched = None
    if packfilter["filters"] is not None:
        from fnmatch import fnmatch
        for pattern in packfilter["filters"]:
            if fnmatch(funcname, pattern):
                matched = True
                return matched

    #We don't have any use cases yet for regex filters.
    if packfilter["rfilters"] is not None: # pragma: no cover
        for pattern in packfilter["rfilters"]:
            if pattern.match(funcname):
                matched = True
                return matched

    if packfilter["ignores"] is not None:
        from fnmatch import fnmatch
        for pattern in packfilter["ignores"]:
            if fnmatch(funcname, pattern):
                matched = False
                return matched

    if packfilter["rignores"] is not None: # pragma: no cover
        for pattern in packfilter["rignores"]:
            if pattern.match(funcname):
                matched = False
                return matched

    if matched is None:
        matched = not explicit
            
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
        elif isinstance(instance, tuple):
            return instance
        else:
            return instance.uuid
    else:
        #Must be a simple built-in type like `int` or `float`, in which case we
        #don't want to convert it to a string.
        return item
    
def _check_args(*argl, **argd):
    """Checks the specified argument lists for objects that are trackable.
    """
    args = {"_": []}
    for item in argl:
        args["_"].append(_tracker_str(item))
           
    for key, item in argd.items():
        args[key] = _tracker_str(item)
        
    return args

def _decorated_path(spath, ipython=True):
    """Checks whether the specified code path is from a package that has been
    decorated by `acorn`.

    Args:
        spath (str): path to the module code file where the function was
          defined.
        ipython (bool): when True, any code source paths in the stack with
          "ipython-input" in the path are included as well.
    """
    #When multiple packages are decorated, the stacks can become interdependent;
    #in that case, it isn't good enough to just check the package name from the
    #fqdn of the function being called.
    return any([p in spath for p in _pack_paths])

def _reduced_stack(istart=3, iend=5, ipython=True):
    """Returns the reduced function call stack that includes only relevant
    function calls (i.e., ignores any that are not part of the specified package
    or acorn.

    Args:
        package (str): name of the package that the logged method belongs to.
    """
    import inspect
    return [i[istart:iend] for i in inspect.stack() if _decorated_path(i[1])]

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

def _pre_create(cls, atdepth, stackdepth, *argl, **argd):
    """Checks whether the the logging should happen based on the specified
    parameters. If it should, an initialized entry is returned.
    """
    from time import time
    if not atdepth:
        rstack = _reduced_stack()
        reduced = len(rstack)
        if msg.will_print(3): # pragma: no cover
            sstack = [' | '.join(map(str, r)) for r in rstack]
            msg.info("{} => stack ({}): {}".format(cls.__fqdn__, len(rstack),
                                                   ', '.join(sstack)), 3)
    else:
        reduced = stackdepth + 10

    if reduced <= stackdepth:
        args = _check_args(*argl, **argd)
        entry = {
            "m": "{}.__new__".format(cls.__fqdn__),
            "a": args,
            "s": time(),
            "r": None,
            "stack": reduced
            }
    else:
        atdepth = True
        entry = None

    return (entry, atdepth)

def _post_create(atdepth, entry, result):
    """Finishes the entry logging if applicable.
    """
    if not atdepth and entry is not None:
        if result is not None:
            #We need to get these results a UUID that will be saved so that any
            #instance methods applied to this object has a parent to refer to.
            retid = _tracker_str(result)
            entry["r"] = retid
            ekey = retid
        else: # pragma: no cover
            ekey = _tracker_str(cls)

        msg.info("{}: {}".format(ekey, entry), 1)
        record(ekey, entry)
        
def creationlog(base, package, stackdepth=_def_stackdepth):
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
        global _atdepth_new, _cstack_new, streamlining
        origstream = None
        if not (decorating or streamlining):
            entry, _atdepth_new = _pre_create(cls, _atdepth_new,
                                              stackdepth, *argl, **argd)
            _cstack_new.append(cls)

            #See if we need to enable streamlining for this constructor.
            fqdn = cls.__fqdn__
            if fqdn in _streamlines and _streamlines[fqdn]:
                #We only use streamlining for the plotting routines at the
                #moment, so it doesn't get hit by the unit tests.
                msg.std("Streamlining {}.".format(fqdn), 2)
                origstream = streamlining
                streamlining = True
            
        try:
            if six.PY2:
                result = base.__old__(cls, *argl, **argd)
            else: # pragma: no cover
                #Python 3 changed the way that the constructors behave. In cases
                #where a class inherits only from object, and doesn't override
                #the __new__ method, the __old__ we replaced was just the one
                #belonging to object.
                if base.__old__ is object.__new__:
                    result = base.__old__(cls)
                else:
                    result = base.__old__(cls, *argl, **argd)
                    
        except TypeError: # pragma: no cover
            #This is a crazy hack! We want this to be dynamic so that it can
            #work with any of the packages. If the error message suggests using
            #a different constructor, we go ahead and use it.
            import sys
            xcls, xerr = sys.exc_info()[0:2]
            referral = xerr.args[0].split()[-1]
            if ".__new__()" in referral:
                t = eval(referral.split('.')[0])
                result = t.__new__(cls, *argl, **argd)
            else:
                raise
                result = None

        if result is not None and hasattr(cls, "__init__"):
            try:
                cls.__init__(result, *argl, **argd)
            except: # pragma: no cover
                print(cls, argl, argd)
                raise
        else: # pragma: no cover
            msg.err("Object initialize failed for {}.".format(base.__name__))

        #If we don't disable streamlining for the original method that set
        #it, then the post call would never be reached.
        if origstream is not None:
            #We avoid another dict lookup by checking whether we set the
            #*local* origstream to something above.
            streamlining = origstream
            
        if not (decorating or streamlining):
            _cstack_new.pop()
            if len(_cstack_new) == 0:
                _atdepth_new = False
            _post_create(_atdepth_new, entry, result)
                        
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

def _pre_call(atdepth, parent, fqdn, stackdepth, *argl, **argd):
    """Checks whether the logging should create an entry based on stackdepth. If
    so, the entry is created.
    """
    from time import time
    if not atdepth:
        rstack = _reduced_stack()
        if "<module>" in rstack[-1]: # pragma: no cover
            code = rstack[-1][1]
        else:
            code = ""

        reduced = len(rstack)
        if msg.will_print(3): # pragma: no cover
            sstack = [' | '.join(map(str, r)) for r in rstack]
            msg.info("{} => stack ({}): {}".format(fqdn, len(rstack),
                                             ', '.join(sstack)), 3)
    else:
        reduced = stackdepth + 10

    bound = False
    if reduced <= stackdepth:
        args = _check_args(*argl, **argd)
        # At this point, we should start the entry. If the method raises an
        # exception, we should keep track of that. If this is an instance
        # method, we should get its UUID, if not, then we can just store the
        # entry under the full method name.

        #There is yet another subtletly here: many packages have a base, static
        #method that gets set as an instance method for sub-classes of a certain
        #ABC. In that case, parent will be a super-class of the first argument,
        #though the types will *not* be identical. Check for overlap in the base
        #classes of the first argument. It would be nice if we could easily
        #check for bound methods using inspect, but it doesn't work for some of
        #the C-extension modules...
        if (len(argl) > 0 and parent is not None and inspect.isclass(parent)):
            ftype = type(argl[0])
            if isinstance(argl[0], parent):
                bound = True
            elif (inspect.isclass(ftype) and hasattr(ftype, "__bases__") and
                inspect.isclass(parent) and hasattr(parent, "__bases__")): # pragma: no cover
                common = set(ftype.__bases__) & set(parent.__bases__)
                bound = len(common) > 0
                
        if not bound:
            #For now, we use the fqdn; later, if the result is not None, we
            #will rather index this entry by the returned result, since we
            #can also access the fqdn in the entry details.
            ekey = fqdn
        else:
            # It must have the first argument be the instance.
            ekey = _tracker_str(argl[0])

        #Check whether the logging has been overidden by a configuration option.
        if (fqdn not in _logging or _logging[fqdn]):
            entry = {
                "m": fqdn,
                "a": args,
                "s": time(),
                "r": None,
                "c": code,
            }
        else:
            entry = None
    else:
        entry = None
        atdepth = True
        ekey = None

    return (entry, atdepth, reduced, bound, ekey)

def _post_call(atdepth, package, fqdn, result, entry, bound, ekey, argl, argd):
    """Finishes constructing the log and records it to the database.
    """
    from time import time
    if not atdepth and entry is not None:
        ek = ekey
        if result is not None:
            retid = _tracker_str(result)
            if result is not None and not bound:
                ek = retid
                entry["r"] = None
            else:
                entry["r"] = retid
            
        name = fqdn.split('.')[-1]
        if filter_name(fqdn, package, "time"):
            entry["e"] = time() - entry["s"]
        if filter_name(fqdn, package, "analyze"):
            entry["z"] = analyze(fqdn, result, argl, argd)

        msg.info("{}: {}".format(ek, entry), 1)
        # Before we return the result, let's first save this call to the
        # database so we have a record of it.
        record(ek, entry)
        return (ek, entry)
    else:
        return (None, None)    

def post(fqdn, package, result, entry, bound, ekey, *argl, **argd):
    """Adds logging for the post-call result of calling the method externally.

    Args:
        fqdn (str): fully-qualified domain name of the function being logged.
        package (str): name of the package we are logging for. Usually the first
          element of `fqdn.split('.')`.
        result: returned from calling the method we are logging.
        entry (dict): one of the values returned by :func:`pre`.
        bound (bool): true if the method is bound.
        ekey (str): key under which to store the entry in the database.
    """
    global _atdepth_call, _cstack_call
    _cstack_call.pop()
    if len(_cstack_call) == 0:
        _atdepth_call = False
    r = _post_call(_atdepth_call, package, fqdn, result,
                   entry, bound, ekey, argl, argd)
    return r
        
def pre(fqdn, parent, stackdepth, *argl, **argd):
    """Adds logging for a call to the specified function that is being handled
    by an external module.

    Args:
        fqdn (str): fully-qualified domain name of the function being logged.
        parent: *object* that the function belongs to.
        stackdepth (int): maximum stack depth before entries are ignored.
        argl (list): positional arguments passed to the function call.
        argd (dict): keyword arguments passed to the function call.
    """
    global _atdepth_call, _cstack_call
    #We add +1 to stackdepth because this method had to be called in
    #addition to the wrapper method, so we would be off by 1.
    pcres = _pre_call(_atdepth_call, parent, fqdn, stackdepth+1,
                      *argl, **argd)
    entry, _atdepth_call, reduced, bound, ekey = pcres
    _cstack_call.append(fqdn)
    return (entry, bound, ekey)

class CallingDecorator(object):
    """Decorator for wrapping package library methods for intelligent
    logging.
    
    Args:
        func (function): the function to wrap with a logging decorator.

    Examples:
        Replace a function `myfunc` that was declared in a module `mymod` with a
        decorated version. The fully-qualified name of the object can be queried
        using :func:`acorn.logging.decoration._fqdn`.

        >>> from acorn.logging.decoration import CallingDecorator as CD
        >>> decor = CD(myfunc)
        >>> setattr(mymod, "myfunc", decor(fqdn, package, None))
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, fqdn, package, parent, stackdepth=_def_stackdepth):
        """Constructs a calling wrapper for the specified reference to
        :attr:`func`.

        Args:
            fqdn (str): fully qualified name of the method being decorated.
            package (str): name of the package the `func` belongs to.
            parent: class to which `func` belongs if it exists.
            stackdepth (int): if the calling stack is less than this depth, than
              include the entry in the log; otherwise ignore it.

        Returns:
            function: the wrapper that logs before and after the function call
              based on package settings.
        """
        def wrapper(*argl, **argd):
            global streamlining, _cstack_call
            origstream = None
            if not (decorating or streamlining):
                entry, bound, ekey = pre(fqdn, parent, stackdepth, *argl,**argd)

                #See if we need to enable streamlining for this method call.
                if fqdn in _streamlines and _streamlines[fqdn]:
                    msg.std("Streamlining {}.".format(fqdn), 2)
                    origstream = streamlining
                    streamlining = True
                    
            #There is a terrible subtlety here. Some packages use the
            #exceptions to figure out what to do next. Scenario: a package
            #calls a method and has several `except` statements to handle
            #the exceptions it raises and make decisions. We *wrap* the
            #specified method and then catch the exception here. If we don't
            #bubble the exception up, then it won't be able to handle it. If
            #we do, then actual exceptions that get raised could break the
            #acorn logging.
            
            #Just let the call do whatever it wants to. The difficulty now
            #is that if this method raises an exception, we never get to the
            #post() call below that pops this method off the call stack. So,
            #forever after, we will be at depth and nothing will log... If
            #we pop the call here, then there was no real point in pushing
            #it in the first place. So, we try the method; if it fails, we
            #pop the call stack and then raise the exception to bubble it
            #up.
            try:
                result = self.func(*argl, **argd)
            except:
                if len(_cstack_call) > 0:
                    _cstack_call.pop()
                if not testmode and not(decorating or streamlining):
                    import sys
                    xt, xm = sys.exc_info()[0:2]
                    error = "{}('{}')".format(xt.__name__, ', '.join(xm))
                    if entry is not None:
                        entry["!"] = error
                raise    
                
            #NOTE: it may seem clever to enable the streamlining here as well,
            #however, this ends up causing infinite recursion loops because
            #methods like np.array need to end up being of the sub-classed
            #ndarray type before the decorators will quit.
            if not decorating:
                if fqdn in _callwraps:
                    result = _callwraps[fqdn](result)

            #If we don't disable streamlining for the original method that set
            #it, then the post call would never be reached.
            if origstream is not None:
                #We avoid another dict lookup by checking whether we set the
                #*local* origstream to something above.
                streamlining = origstream
                    
            if not (decorating or streamlining):
                post(fqdn, package, result, entry, bound, ekey, *argl, **argd)
            return result

        _safe_setattr(wrapper, "__acorn__", self.func)
        setattr(wrapper, "__getattribute__", _safe_getattr(wrapper))
        
        return wrapper

_extended_objs = {}
"""dict: keys are :func:`id` memory addresses of objects; values are the
*extended* objects that `acorn` created.
"""
_final_objs = []
"""list: of :func:`id` memory addresses of objects; these are objects marked as
final that cannot be subclassed and also cannot have their attributes set.
"""
def _create_extension(o, otype, fqdn, pmodule):
    """Creates an extension object to represent `o` that can have attributes
    set, but which behaves identically to the given object.

    Args:
        o: object to create an extension for; no checks are performed to see if
          extension is actually required.
        otype (str): object types; one of ["classes", "functions", "methods",
          "modules"].
        fqdn (str): fully qualified name of the package that the object belongs
          to.
        pmodule: the parent module (or class) that `o` belongs to; used for setting
          the special __module__ attribute.
    """
    import types
    xdict = {"__acornext__": o,
             "__doc__": o.__doc__}

    if otype == "classes":
        classname = o.__name__
        try:
            if fqdn in _explicit_subclasses:
                xclass = eval(_explicit_subclasses[fqdn])
                xclass.__acornext__ = o
            else:
                xclass = type(classname, (o, ), xdict)
            xclass.__module__ = o.__module__
            return xclass
        except TypeError:
            #This happens when a class is final, meaning that it is not allowed
            #to be subclassed.
            _final_objs.append(id(o))
            return o
    elif (otype in ["functions", "descriptors", "unknowns"] or
          (otype == "builtins" and (isinstance(o, types.BuiltinFunctionType) or
                                    isinstance(o, types.BuiltinMethodType)))):
        #The unknowns type is for objects that don't match any of the
        #inspect.is* function calls, but still have a __call__ method (such as
        #the numpy.ufunc class instances). These can still be wrapped by another
        #function.
        def xwrapper(*args, **kwargs):
            try:
                return o(*args, **kwargs)
            except:
                #see issue #4.
                targs = list(map(type, args))
                kargs = list(kwargs.keys())
                msg.err("xwrapper: {}({}, {})".format(o, targs, kargs), 2)
                pass
            
        #Set the docstring and original object attributes.
        for attr, val in xdict.items():
            setattr(xwrapper, attr, val)
            
        #We want to get the members dictionary. For classes, using
        #:meth:`inspect.getmembers` produces stack overflow errors. Instead, we
        #reference the __dict__ directly. However, for built-in methods and
        #functions, there is no __dict__, so we use `inspect.getmembers`.
        failed = False
        setattr(xwrapper, "__getattribute__", _safe_getattr(xwrapper))

        #We want the new function to be identical to the old except that
        #it's __call__ method, which we overrode above.
        failed = not _update_attrs(xwrapper, o, ["__call__"])

        if otype in ["descriptors", "unknowns"] and inspect.ismodule(pmodule):
            if hasattr(o, "__objclass__"): # pragma: no cover
                setattr(xwrapper, "__module__", pmodule.__name__)
            elif hasattr(o, "__class__") and o.__class__ is not None:
                setattr(xwrapper, "__module__", pmodule.__name__)

        if not failed:
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
            if isinstance(obj, dict): # pragma: no cover
                obj[name] = value
            else:
                setattr(obj, name, value)
            return True
    except (TypeError, AttributeError):
        _set_failures.append(okey)
        msg.warn("Failed {}:{} attribute set on {}.".format(name, value, obj))
        return False
    
def _extend_object(parent, n, o, otype, fqdn):
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
        fqdn (str): fully qualified name of the package that the object belongs
          to.
    """
    from inspect import ismodule, isclass
    pmodule = parent if ismodule(parent) or isclass(parent) else None
    try:
        #The __acornext__ attribute references the original, unextended
        #object; if the object didn't need extended, then __acornext__ is
        #none.
        if otype == "methods":
            setattr(o.__func__, "__acornext__", None)
        else:
            setattr(o, "__acornext__", None)

        fqdn = _fqdn(o, recheck=True, pmodule=pmodule)
        return o
    except (TypeError, AttributeError):
        #We have a built-in or extension type. 
        okey = id(o)
        if okey not in _extended_objs:
            #We need to generate an extension for this object and store it
            #in the extensions dict.
            xobj = _create_extension(o, otype, fqdn, pmodule)
            fqdn = _fqdn(xobj, recheck=True, pmodule=pmodule)
            if xobj is not None:
                _extended_objs[okey] = xobj
            #else: we can't handle this kind of object; it just won't be
            #logged...
        try:
            setattr(parent, n, _extended_objs[okey])
            return _extended_objs[okey]
        except KeyError: # pragma: no cover
            msg.warn("Object extension failed: {} ({}).".format(o, otype))

def _get_members(o):
    """Returns the likely members of the object by appealing to :func:`dir`
    instead of using `__dict__` attribute, since that misses certain members.
    """
    result = []
    for n in dir(o):
        if hasattr(o, n) and n not in ["__globals__", "func_globals"]:
            result.append((n, getattr(o, n)))
    return result

_split_objects = []
"""list: of objects that have had split called already. This allows us to handle
objects that would recursively refer to parents that have already been split.
"""
def _split_object(pobj, package, resplit=False, packincl=None, skipext=False):
    """Splits the specified object into its modules, classes, methods and
    functions so that it can be decorated more easily. For extension
    modules/classes that can't have attributes set, the object's dictionary is
    modified to point to a derived-type version.

    Args:
        pobj: object instance returned from the import.
        package (str): name of the package (used for filtering all the loaded
          packages and methods inside the package object).
        resplit (bool): if True, re-processes the object, even if has been done
          before.
        packincl (list): of package names that should be considered relevant when
          deciding how to filter the members of this object. If a member belongs
          to one of these packages, they will be included in the split for the
          object.
        skipext (bool): when True, the list of split objects is only returned;
          no attempts are made to extend any objects for decoration.
    """
    import inspect
    result = {
        "classes": [],
        "functions": [],
        "methods": [],
        "modules": [],
        "builtins": [],
        "descriptors": [],
        "unknowns": []
        }

    global _split_objects
    if pobj in _split_objects and not resplit:
        return result
    
    tests = {
        "classes": inspect.isclass,
        "functions": inspect.isfunction,
        "methods": inspect.ismethod,
        "modules": inspect.ismodule,
        "builtins": inspect.isbuiltin,
        "descriptors": inspect.ismethoddescriptor
        }

    from functools import partial
    prepack = "{}.".format(package)
    pms = []
    pmodule = pobj if inspect.ismodule(pobj) or inspect.isclass(pobj) else None
    for n, o in _get_members(pobj):
        if isinstance(o, (dict, list, set, float, int, str, complex, bool)):
            #We are looking for functions, modules and packages; sometimes
            #constants are declared that we just ignore.
            continue
        else:
            omod = _safe_getmodule(o)
            if omod is None:
                #This may be an instance method of an object-class. In that
                #case, we still want to decorate it.
                if hasattr(o,"__objclass__") and o.__objclass__ is not type:
                    omod = _safe_getmodule(o.__objclass__)
                elif hasattr(o, "__class__") and o.__class__ is not type:
                    omod = _safe_getmodule(o.__class__)
                else:
                    omod = pmodule

                #Catch the last outlier case: C-extension built-in descriptors
                #methods for "built-in" objects.
                if omod is None and inspect.ismethoddescriptor(o):
                    omod = pmodule
                    
        #Some packages define special types with __class__ = type. These are
        #indistinguishable from the built-in types like `float` or `str`. So we
        #force the developers to configure these manually.
        packok = False
        confok = False
        pincl = False        
        if omod is not None:
            if packincl is not None and len(packincl) > 0:
                #We want to sometimes return all the objects available at the
                #top-level of a package, even if they were imported from a
                #different package. This doesn't get called in normal decoration
                #mode, except for certain special packages.
                fqdn_ = _fqdn(o, False, pmodule=pmodule)
                if fqdn_ is not None:
                    pincl = any(p in fqdn_ for p in packincl)

            omodname = (omod.__name__ if inspect.ismodule(omod)
                        else _fqdn(omod, False))
            packok = (prepack in omodname or omodname == package or pincl)
            if not packok and hasattr(o, "__class__") and o.__class__ is type:
                fqdn_ = _fqdn(o, False, pmodule=pmodule)
                incl = filter_name(fqdn_, package, explicit=True)
                if incl: # pragma: no cover
                    filesrc = inspect.getabsfile(pobj)
                    confok = "/{}/".format(package) in filesrc
                
        if packok or confok:
            pms.append((n, o, confok))                    

    global _decor_count
    def oappend(n, o, t, result, confok):
        """Appends the specified object to `results` if it can be extended.

        Args:
            confok (bool): when True, the code has already determined previously
              that this object should be decorated no matter what (the user said
              so). In that case, we bypass the regular name checks.
        """
        fqdn = _fqdn(o, False, pmodule=pmodule)
        if fqdn is None:
            #The object was probably of type unknown and doesn't have a __name__
            #attribute, so we just skip it.
            return

        package = fqdn.split('.')[0]
        if confok or (filter_name(n, package) and filter_name(fqdn, package)):
            xobj = _extend_object(pobj, n, o, t, fqdn)
            if xobj is not None:
                result[t].append((n, xobj))
            else: # pragma: no cover
                msg.warn("Couldn't extend {} ({}).".format(o, t), 2)
        else:
            skipmsg = "Skipping {}: {} because of filter rules."
            msg.info(skipmsg.format(n, fqdn), 4)
            if package in _decor_count:
                _decor_count[package][1] += 1
        
    for n, o, confok in pms:
        for t, f in tests.items():
            if f(o):
                if skipext:
                    result[t].append((n, o))
                else:
                    oappend(n, o, t, result, confok)
                break
        else:
            #With some class instances (which end up being members of
            #objects), an error is raised because they implement their own
            #__getattr__ routine that wasn't designed to work with acorn. We
            #just ignore these. We don't want to decorate object instances
            #anyway, except that numpy.ufunc instances are actually
            #functions that don't match any of the inspect.is* methods, and
            #so we have this catch-all over here.
            cancall = _safe_hasattr(o, "__call__")
            if cancall:
                if skipext: # pragma: no cover
                    result["unknowns"].append((n, o))
                else:
                    oappend(n, o, "unknowns", result, confok)

    _split_objects.append(pobj)
    return result

def _fqdn(o, oset=True, recheck=False, pmodule=None):
    """Returns the fully qualified name of the object.

    Args:
        o (type): instance of the object's type.
        oset (bool): when True, the fqdn will also be set on the object as attribute
          `__fqdn__`.
        recheck (bool): for sub-classes, sometimes the super class has already had
          its __fqdn__ attribute set; in that case, we want to recheck the
          object's name. This usually only gets used during object extension.
    """
    if id(o) in _set_failures or o is None:
        return None
    
    if recheck or not _safe_hasattr(o, "__fqdn__"):
        import inspect
        if not hasattr(o, "__name__"):
            msg.warn("Skipped object {}: no __name__ attribute.".format(o), 3)
            return
        
        result = None
        if hasattr(o, "__acornext__") and o.__acornext__ is not None:
            otarget = o.__acornext__
        else:
            otarget = o
            
        omod = _safe_getmodule(otarget) or pmodule
        if (omod is None and hasattr(otarget, "__objclass__") and
            otarget.__objclass__ is not None): # pragma: no cover
            omod = _safe_getmodule(otarget.__objclass__)
            parts = ("<unknown>" if omod is None else omod.__name__,
                     otarget.__objclass__.__name__,
                     otarget.__name__)
            #msg.std("FQDN: objclass => {}".format(parts), 4)
            result = "{}.{}.{}".format(*parts)
        elif (omod is None and hasattr(otarget, "__class__") and
              otarget.__class__ is not None):
            omod = _safe_getmodule(otarget.__class__)
            parts = ("<unknown>" if omod is None else omod.__name__,
                     otarget.__class__.__name__,
                     otarget.__name__)
            #msg.std("FQDN: class => {}".format(parts), 4)
            result = "{}.{}.{}".format(*parts)
        elif omod is not otarget:
            parts = (_fqdn(omod, False), otarget.__name__)
            #msg.std("FQDN: o => {}".format(parts), 4)
            result = "{}.{}".format(*parts)
        else:
            result = otarget.__name__

        if oset:
            _safe_setattr(o, "__fqdn__", result)
        return result

    if _safe_hasattr(o, "__fqdn__"):
        return o.__fqdn__

_stack_config = {}
"""dict: keys are package names, values are :type:`dict` where the keys are
fqdns of package members and values are the configured stack depths.
"""
def _get_stack_depth(package, fqdn, defdepth=_def_stackdepth):
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
        _stack_config[package] = {}

        secname = "logging.depth"
        if spack.has_section(secname):
            for ofqdn in spack.options(secname):
                _stack_config[package][ofqdn] = spack.getint(secname, ofqdn)

    usedef = True
    if fqdn in _stack_config[package]:
        result = _stack_config[package][fqdn]
        usedef = False
    elif "*" in _stack_config[package]: # pragma: no cover
        result = _stack_config[package]["*"]
        usedef = False
    else:
        result = defdepth

    if not usedef:
        msg.gen("Using {} for {} stack depth.".format(result, fqdn), 3)
    return result

_decor_count = {"__builtin__": [0,0,0], "__main__": [0,0,0]}
"""dict: keys are package names, values are list [decorated, skipped, na] that
keeps statistics on how many of the package objects actually get decorated.
"""
_decorated_o = {"__builtin__": {}, "__main__": {}}
"""dict: keys are package names; values are dicts with keys :func:`id` values
for all the objects that have been decorated already. Introduced so that classes
which inherit from already decorated classes won't be skipped for already having
__acorn__ on them.

"""
    
def decorate_obj(parent, n, o, otype, recurse=True, redecorate=False):
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

    Examples:
        Decorate the function `mymod.myfunc` to log automatically to the
        database.

    >>> from acorn.logging.decoration import decorate_obj
    >>> import mymod
    >>> decorate_obj(mymod, "myfunc", mymod.myfunc, "functions")

    """
    global _decor_count, _decorated_o
    from inspect import isclass, isfunction, ismodule
    pmodule = parent if ismodule(parent) or isclass(parent) else None
    fqdn = _fqdn(o, recheck=True, pmodule=pmodule)
    if fqdn is None:
        #This object didn't have a name, which means we can't extend it or
        #track it anyway.
        return

    package = fqdn.split('.')[0]
    d = _get_stack_depth(package, fqdn)
    if (package in _decorated_o and
        (id(o) not in _decorated_o[package] or redecorate)):
        decor = None
        if hasattr(o, "__call__") and otype != "classes":
            #calling on class types is handled by the construction decorator
            #below.
            cdecor = CallingDecorator(o)
            if isclass(parent):
                clog = cdecor(fqdn, package, parent, d)
            else:
                clog = cdecor(fqdn, package, None, d)

            #We can't update the attributes of the static methods (it just
            #produces errors), so we do what we can before that.
            msg.std("Setting decorator on {}.".format(fqdn), 4)
            _update_attrs(clog, o)
            if ((hasattr(o, "im_self") and o.im_self is parent)):
                clog = staticmethod(clog)
            setok = _safe_setattr(parent, n, clog)

            if setok:
                decor = cdecor
                msg.okay("Set calling logger on {}: {}.".format(n, fqdn), 3)
            _decor_count[package][0] += 1
        else:
            setok = _safe_setattr(o, "__acorn__", None)
            _decor_count[package][2] += 1

        if otype == "classes" and setok:
            if hasattr(o, "__new__"):
                setattr(o, "__old__", staticmethod(o.__new__))
                crelog = creationlog(o, package, d)
                setok = _safe_setattr(o, "__new__", creationlog(o, package, d))
                
                if setok:
                    decor = crelog
                    msg.gen("Set creation logger on {}: {}.".format(n, fqdn),3)
                _decor_count[package][0] += 1
            #else: must have only static methods and no instances.
            
        if setok:
            _decorated_o[package][id(o)] = decor
        else:
            _decorated_o[package][id(o)] = None

        #We don't need to bother recursing for those modules/classes that
        #can't have their attributes set, since their members will have the
        #same restrictions.
        if setok and otype in ["classes", "modules"]:
            #These types can be further decorated; let's traverse their members
            #and try to decorate those as well.
            splits = _split_object(o, package)
            for ot, ol in splits.items():
                for nobj, obj in ol:
                    decorate_obj(o, nobj, obj, ot)
            
    elif otype != "classes" and package in _decorated_o:
        #Even though the object with that id() has been decorated, it doesn't
        #mean that the parent has had its attribute overwritten to point to the
        #decorated object. This happens with instance methods on different
        #classes that are implemented by another generic method.
        target = _decorated_o[package][id(o)]
        child = getattr(parent, n)
        if target is not None:
            clog = target(fqdn, package, parent)
            _safe_setattr(clog, "__acorn__", o)
            _update_attrs(clog, o)
            
            setok = _safe_setattr(parent, n, clog)
            msg.okay("Set existing calling logger on {}: {}.".format(n,fqdn), 4)

_explicit_subclasses = {}
"""dict: keys are fqdns values are the fqdn to the acorn, hand-coded
subclass to use instead of the automatic one.
"""
def _load_subclasses(package):
    """Loads the subclass settings for the specified package so that we can
    decorate the classes correctly.
    """
    global _explicit_subclasses
    from acorn.config import settings
    spack = settings(package)
    if spack is not None:
        if spack.has_section("subclass"):
            _explicit_subclasses.update(dict(spack.items("subclass")))

def _load_generic(packname, package, section, target):
    """Loads the settings for generic options that take FQDN and a boolean value
    (1 or 0).

    Args:
        packname (str): name of the package to get config settings for.
        package: actual package object.
    """
    from acorn.config import settings
    spack = settings(packname)
    if spack.has_section(section):
        secitems = dict(spack.items(section))
        for fqdn, active in secitems.items():
            target[fqdn] = active == "1"
            
_logging = {}
"""dict: keys are functions fqdns; values are `bool`, indicating whether the
method should be logged. This enables functions to be tracked (for example to
enable streamlining of sub-calls that *are* normally logged) but prevents them
from producing entries in the database.
"""
def _load_logging(packname, package):
    """Loads the settings for methods that should *not* be logged, even though
    they are being tracked.

    Args:
        packname (str): name of the package to get config settings for.
        package: actual package object.
    """
    global _logging
    _load_generic(packname, package, "logging", _logging)

_streamlines = {}
"""dict: keys are function fqdns; values are `bool`, indicating whether the
method should streamline all subsequent method calls.
"""
def _load_streamlines(packname, package):
    """Loads the settings for methods that should streamline subsequent method
    calls. This is useful for methods that have thousands of sub-calls and wish
    to avoid checking the stack depth at each of those.

    Args:
        packname (str): name of the package to get config settings for.
        package: actual package object.
    """
    global _streamlines
    _load_generic(packname, package, "streamline", _streamlines)

_callwraps = {}
"""dict: keys are function fqdns; values are other function, class or method
fqdns that will be called to wrap the result of the original function call
before returning.
"""
def _load_callwraps(packname, package):
    """Loads the special call wrapping settings for functions in the specified
    package. This allows the result of the original method call to be cast as a
    different type, or passed to a different constructor before returning from
    the wrapped function.

    Args:
        packname (str): name of the package to get config settings for.
        package: actual package object.
    """
    global _callwraps
    from acorn.config import settings
    from acorn.logging.descriptors import _obj_getattr
    spack = settings(packname)
    if spack is not None:
        if spack.has_section("callwrap"):
            wrappings = dict(spack.items("callwrap"))
            for fqdn, target in wrappings.items():
                caller = _obj_getattr(package, target)
                _callwraps[fqdn] = caller

def set_decorating(decorating_):
    """Sets whether the module is operating in decorating mode.
    """
    global decorating
    decorating = decorating_
                
def decorate(package):
    """Decorates all the methods in the specified package to have logging
    enabled according to the configuration for the package.
    """
    from os import sep
    global _decor_count, _decorated_packs, _decorated_o, _pack_paths
    global decorating
    if "acorn" not in _decorated_packs:
        _decorated_packs.append("acorn")
        packpath = "acorn{}".format(sep)
        if packpath not in _pack_paths:
            #We initialize _pack_paths to include common packages that people
            #use without decorating. Otherwise those slow *way* down and the
            #notebook becomes unusable.
            _pack_paths.append(packpath)
        
    npack = package.__name__
    #Since scipy includes numpy (for example), we don't want to run the numpy
    #decoration twice if the person also chooses to import numpy. In that case,
    #we just skip it; the memory references in scipy point to the same numpy
    #modules and libraries.
    if npack not in _decorated_packs:
        _decor_count[npack] = [0, 0, 0]
        _decorated_o[npack] = {}
        _load_subclasses(npack)
        
        packsplit = _split_object(package, package.__name__)
        origdecor = decorating
        decorating = True
        
        for ot, ol in packsplit.items():
            for name, obj in ol:
                decorate_obj(package, name, obj, ot)

        #Now that we have actually decorated all the objects, we can load the
        #call wraps to point to the new decorated objects.
        _load_callwraps(npack, package)
        _load_streamlines(npack, package)
        _load_logging(npack, package)
        decorating = origdecor
        _decorated_packs.append(npack)
        _pack_paths.append("{}{}".format(npack, sep))
        msg.info("{}: {} (Decor/Skip/NA)".format(npack, _decor_count[npack]))

def postfix(package):
    """Makes sure that any additional imported names in the specified package
    that were decorated in the context of a *different* package still get
    redirected to the decorated objects.

    Args:
        package: package object to examine for compliance.

    Examples:
    When `scipy` is imported, it imports most of `numpy` automatically and then
    has references to the original, *undecorated* `numpy` functions. We use
    :func:`postfix` to set the `scipy` references to the decorated `numpy`
    functions.

    >>> import scipy
    >>> import acorn.numpy
    >>> from acorn.logging.decoration import postfix, decorate
    >>> decorate(scipy)
    >>> postfix(scipy)

    When we call :func:`decorate` on `scipy`, the references to `numpy`
    functions are ignored, because they don't belong to the `scipy`
    package. This filtering is a feature to prevent `acorn` repeatedly visiting
    commonly used modules that are imported.
    """
    #This time we don't have to go recursively; we can just look at top-level
    #objects in the package.
    global decorating
    origdecor = decorating
    decorating = True
    
    packsplit = _split_object(package, package.__name__,
                              resplit=True, packincl=["numpy"], skipext=True)
    for ot, ol in packsplit.items():
        for name, obj in ol:
            if hasattr(obj, "__acorn__") or hasattr(obj, "__acornext__"):
                continue

            #The object could have been decorated directly, *or* it could have
            #been extended first, and then decorated.
            key = id(obj)
            fqdn_ = _fqdn(obj, False)
            if fqdn_ is None: # pragma: no cover
                continue

            packname = fqdn_.split('.')[0]
            if key not in _decorated_o[packname] and key in _extended_objs:
                xobj = _extended_objs[key]
                key = id(xobj)

            if key in _decorated_o[packname]:
                target = _decorated_o[packname][key]
                if target is not None and isinstance(target, CallingDecorator):
                    clog = target(fqdn_, packname, None)
                    _safe_setattr(clog, "__acornext__", obj)
                    _update_attrs(clog, obj)

                    setattr(package, name, clog)
                    dmsg = "Postfix decorated {} to {}."
                    msg.info(dmsg.format(name, target), 3)
    decorating = origdecor
