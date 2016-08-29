"""Methods for describing the objects within packages that are not instantiated
by the user in the scope of __main__.
"""
_package_desc = {}
"""dict: keys are package names, values are dictionaries with object FQDN as
keys, and values being a list of attributes and transform functions needed to
describe the object.
"""

def describe(o):
    """Describes the object using developer-specified attributes specific to
    each main object type.
    """
    #First, we need to determine the fqdn, so that we can lookup the format for
    #this object in the config file for the package.
    from inspect import getmodule
    ocls = o.__class__
    fqdn = "{}.{}".format(getmodule(ocls).__name__, ocls.__name__)
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
    node = package
    for chain in fqdn.split('.')[start:]:
        if hasattr(node, chain):
            node = getattr(node, chain)
        else:
            node = None
            break

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

def json_describe(o, fqdn, descriptor=None):
    """Describes the specified object using the directives in the JSON
    `descriptor`, if available.

    Args:
        o: object to describe.
        fqdn (str): fully-qualified domain name of the object.
        descriptor (dict): keys are attributes of `o`; values are transform
          functions to apply to the attribute so that only a single value is
          returned.
    """
    if descriptor is None or not isinstance(descriptor, dict):
        return {"fqdn": fqdn}
    else:
        result = {"fqdn": fqdn}
        for attr, desc in descriptor.items():
            value = getattr(o, attr, "")
            if "transform" in desc:
                for transform in desc["transform"]:
                    if "numpy" == transform[0:len("numpy")]:
                        value = _numpy_transform(transform, value)
                    elif "scipy" == transform[0:len("scipy")]:
                        value = _scipy_transform(transform, value)
                    elif "math" == transform[0:len("math")]:
                        value = _math_transform(transform, value)
                    elif (transform == "self"):
                        args = desc["args"] if "args" in desc else []
                        kwargs = desc["kwargs"] if "kwargs" in desc else {}
                        value = _instance_transform(attr, o, *args, **kwargs)
                        
            if "slice" in desc:
                for si, sl in enumerate(desc["slice"]):
                    if ':' in sl:
                        name, slice = sl.split(':')
                    else:
                        name, slice = str(si), sl

                    slvalue = value
                    for i in map(int, slice.split(',')):
                        slvalue = slvalue[i]

                    result[name] = slvalue
            else:
                if "rename" in desc:
                    result[desc["rename"]] = value
                else:
                    result[attr] = value
                
    return result
