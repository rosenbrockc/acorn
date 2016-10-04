"""Methods for describing the objects within packages that are not instantiated
by the user in the scope of `__main__`.
"""
_package_desc = {}
"""dict: keys are package names, values are dictionaries with object FQDN as
keys, and values being a list of attributes and transform functions needed to
describe the object.
"""

def describe(o):
    """Describes the object using developer-specified attributes specific to
    each main object type.

    Returns:
        dict: keys are specific attributes tailored to the specific object type,
        though `fqdn` is common to all descriptions; values are the corresponding
        attribute values which are *simple* types that can easily be serialized to
        JSON.
    """
    #First, we need to determine the fqdn, so that we can lookup the format for
    #this object in the config file for the package.
    from inspect import getmodule
    from acorn.logging.decoration import _fqdn
    fqdn = _fqdn(o, False)
    if fqdn is None:
        #This should not have happened; if the FQDN couldn't be determined, then
        #we should have never logged it.
        return json_describe(o, str(type(o)))
    package = fqdn.split('.')[0]

    global _package_desc
    if package not in _package_desc:
        from acorn.config import descriptors
        spack = descriptors(package)
        if spack is None:
            _package_desc[package] = None
            return json_describe(o, fqdn)
        else:
            _package_desc[package] = spack
    
    if _package_desc[package] is None:
        return json_describe(o, fqdn)
    elif fqdn in _package_desc[package]:
        return json_describe(o, fqdn, _package_desc[package][fqdn])
    else:
        return json_describe(o, fqdn)

def _obj_getattr(obj, fqdn, start=1):
    """Returns the attribute specified by the fqdn list from obj.
    """
    node = obj
    for chain in fqdn.split('.')[start:]:
        if hasattr(node, chain):
            node = getattr(node, chain)
        else:
            node = None
            break
    return node
    
def _package_transform(package, fqdn, start=1, *args, **kwargs):
    """Applies the specified package transform with `fqdn` to the package.

    Args:
        package: imported package object.
        fqdn (str): fully-qualified domain name of function in the package. If it
          does not include the package name, then set `start=0`.
        start (int): in the '.'-split list of identifiers in `fqdn`, where to start
          looking in the package. E.g., `numpy.linalg.norm` has `start=1` since
          `package=numpy`; however, `linalg.norm` would have `start=0`.
    """
    #Our only difficulty here is that package names can be chained. We ignore
    #the first item since that was already checked for us by the calling
    #method.
    node = _obj_getattr(package, fqdn, start)
    
    #By the time this loop is finished, we should have a function to apply if
    #the developer setting up the config did a good job.
    if node is not None and hasattr(node, "__call__"):
        return node(*args, **kwargs)
    else:
        return args

#It may seem clumsy now to separate all these package transforms out separately
#when we could have handled this easily in _package_transform; however, it will
#likely happen that slight changes need to be made on a per-package basis, so
#separating them out now makes more sense.
def _numpy_transform(fqdn, value):
    """Applies the numpy transform with the specified `fqdn` name to value.

    Args:
        fqdn (str): name of the numpy function to apply to value.
        value: attribute value of the original object to apply function to.
    """
    import numpy
    return _package_transform(numpy, fqdn, value)

def _scipy_transform(fqdn, value):
    """Applies the scipy transform with the specified `fqdn` name to value.

    Args:
        fqdn (str): name of the numpy function to apply to value.
        value: attribute value of the original object to apply function to.
    """
    import scipy
    return _package_transform(scipy, fqdn, value)

def _math_transform(fqdn, value):
    """Applies the math transform with the specified `fqdn` name to value.

    Args:
        fqdn (str): name of the numpy function to apply to value.
        value: attribute value of the original object to apply function to.
    """
    import math
    return _package_transform(math, fqdn, value)

def _instance_transform(fqdn, o, *args, **kwargs):
    """Applies an instance method with name `fqdn` to `o`.

    Args:
        fqdn (str): fully-qualified domain name of the object.
        o: object to apply instance method to.
    """
    return _package_transform(o, fqdn, start=0, *args, **kwargs)

def _array_convert(a):
    """Converts the specified value to a list if it is a :class:`numpy.ndarray`;
    otherwise it is just returned as is.
    """
    from numpy import ndarray
    if isinstance(a, ndarray):
        larr = a.tolist()
        if len(larr) == 1:
            return larr[0]
        else:
            return larr
    else:
        return a

def json_describe(o, fqdn, descriptor=None):
    """Describes the specified object using the directives in the JSON
    `descriptor`, if available.

    Args:
        o: object to describe.
        fqdn (str): fully-qualified domain name of the object.
        descriptor (dict): keys are attributes of `o`; values are transform
          functions to apply to the attribute so that only a single value is
          returned.

    Returns:
        dict: keys are specific attributes tailored to the specific object type,
        though `fqdn` is common to all descriptions; values are the corresponding
        attribute values which are *simple* types that can easily be serialized to
        JSON.
    """
    if descriptor is None or not isinstance(descriptor, dict):
        return {"fqdn": fqdn}
    else:
        result = {"fqdn": fqdn}
        for attr, desc in descriptor.items():
            if attr == "instance":
                #For instance methods, we repeatedly call instance methods on
                #`value`, assuming that the methods belong to `value`.
                value = o
            else:
                if '.' in attr:
                    #We get the chain of attribute values.
                    value = o
                    for cattr in attr.split('.'):
                        if hasattr(value, cattr):
                            value = getattr(value, cattr, "")
                        else:
                            break
                else:
                    #There is just a one-level getattr.    
                    value = getattr(o, attr, "")
                
            if "transform" in desc:
                for transform in desc["transform"]:
                    if "numpy" == transform[0:len("numpy")]:
                        value = _numpy_transform(transform, value)
                    elif "scipy" == transform[0:len("scipy")]:
                        value = _scipy_transform(transform, value)
                    elif "math" == transform[0:len("math")]:
                        value = _math_transform(transform, value)
                    elif "self" in transform:
                        args = desc["args"] if "args" in desc else []
                        kwds = desc["kwargs"] if "kwargs" in desc else {}
                        method = transform[len("self."):]
                        value = _instance_transform(method, value, *args,**kwds)
                        
            if "slice" in desc:
                for si, sl in enumerate(desc["slice"]):
                    if ':' in sl:
                        name, slice = sl.split(':')
                    else:
                        name, slice = str(si), sl

                    slvalue = value
                    for i in map(int, slice.split(',')):
                        slvalue = slvalue[i]
                        
                    result[name] = _array_convert(slvalue)
            else:
                if "rename" in desc:
                    result[desc["rename"]] = _array_convert(value)
                else:
                    result[attr] = _array_convert(value)
                
    return result
