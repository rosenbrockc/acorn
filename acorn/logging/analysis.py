"""Methods for analyzing the results of various calls, specific to each package
and its methods/classes.
"""
_methods = {}
"""dict: keys are package names; values are a dict of `fqdn: method` that shows
which method to use to analyze the result of calling the object with `fqdn`.
"""
def _load_methods(package):
    """Loads the mappings from method call result to analysis.

    Args:
        package (str): name of the package to load for.
    """
    global _methods
    _methods[package] = None
    
    from acorn.config import settings
    from acorn.logging.descriptors import _obj_getattr
    spack = settings(package)
    if spack is not None:
        if spack.has_section("analysis.methods"):
            _methods[package] = {}
            
            from importlib import import_module
            mappings = dict(spack.items("analysis.methods"))
            for fqdn, target in mappings.items():
                rootname = target.split('.')[0]
                root = import_module(rootname)
                caller = _obj_getattr(root, target)
                _methods[package][fqdn] = caller

def analyze(fqdn, result, argl, argd):
    """Analyzes the result from calling the method with the specified FQDN.

    Args:
        fqdn (str): full-qualified name of the method that was called.
        result: result of calling the method with `fqdn`.
        argl (tuple): positional arguments passed to the method call.
        argd (dict): keyword arguments passed to the method call.
    """
    package = fqdn.split('.')[0]
    if package not in _methods:
        _load_methods(package)
        
    if _methods[package] is not None and fqdn in _methods[package]:
        return _methods[package][fqdn](fqdn, result, *argl, **argd)
