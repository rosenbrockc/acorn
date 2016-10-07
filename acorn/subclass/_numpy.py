"""Module for implementing the difficult case of array sub-classing for
numpy. This is necessary because of the C-extension nature of the numpy package
and complications with array slices etc. See
http://docs.scipy.org/doc/numpy/user/basics.subclassing.html.
"""
import numpy as np
import six
from acorn.logging.decoration import decorating, streamlining
def _get_acorn(self, method, *items):
    """Gets either a slice or an item from an array. Used for the __getitem__
    and __getslice__ special methods of the sub-classed array.

    Args:
        method (str): on of ['slice', 'item'].
    """
    #IMPORTANT!! I lost two hours because the ndarray becomes unstable if you
    #don't call the original method first. Somehow passing the array instance to
    #other methods changed its internal representation and made it unusable by
    #the original numpy functions. Putting them first makes it work.
    
    # Because we had to subclass numpy.ndarray, the original methods get
    # stuck in an infinite loop (max. recursion depth exceeded errors). So,
    # we instead grab the reference to the original ndarray object.
    if method == "slice":
        r = np.ndarray.__acornext__.__getslice__(self, *items)
    else:
        r = np.ndarray.__acornext__.__getitem__(self, *items)
        
    if not (decorating or streamlining):
        from acorn.logging.decoration import (pre, post, _fqdn)
        if method == "slice":
            fqdn = "numpy.ndarray.__getslice__"
        else:
            fqdn = "numpy.ndarray.__getitem__"
        preres = pre(fqdn, np.ndarray, 5, self, *items)
        entry, bound, ekey = preres
        # This method can trick acorn into thinking that it is a bound
        # method. We want it to behave like it's not.
        post(fqdn, "numpy", r, entry, np.ndarray, ekey)
    return r 

class ndarray(np.ndarray):
    """Sub-class of :class:`numpy.ndarray` so that we can implement logging for
    the instance method and special method calls of array objects.

    """
    def __new__(cls, input_array):
        from acorn.logging.decoration import set_decorating
        odecor = decorating
        if not decorating:
            set_decorating(True)
            
        #Call the original, undecorated version of asarray.
        if isinstance(input_array, np.ndarray):
            if hasattr(np.ndarray.view, "__acorn__"):
                obj = np.ndarray.view.__acorn__(input_array, cls)
            else:# pragma: no cover
                obj = np.ndarray.view(input_array, cls)
        else:
            if hasattr(np.asarray, "__acorn__"):
                obj = np.asarray.__acorn__(input_array).view(cls)
            else:# pragma: no cover
                obj = np.asarray(input_array).view(cls)

        #We need to make sure that we don't set decor to be False when it was
        #True previously; so we just set it to what it was.
        set_decorating(odecor)
        
        obj.__acorn__ = np.ndarray
        obj.__doc__ = np.ndarray.__doc__
        return obj

    def __getitem__(self, *items):
        return _get_acorn(self, "item", *items)
    
    def __getslice__(self, *items):
        #Unfortunately, we have to implement the slicing here since it does not
        #call any other methods that get decorated.
        return _get_acorn(self, "slice", *items)
    
    def __array_finalize__(self, obj):
        if obj is None: return
        self.__acorn__ = getattr(obj, '__acorn__', None)

    def __array_wrap__(self, outarr, context=None):
        if isinstance(context, tuple):
            from acorn.logging.decoration import (pre, post, _fqdn,
                                                  _def_stackdepth)
            fqdn = _fqdn(context[0], False)
            entry, bound, ekey = pre(fqdn, None, _def_stackdepth, *context[1])

        # Because we had to subclass numpy.ndarray, the original methods get
        # stuck in an infinite loop (max. recursion depth exceeded errors). So,
        # we instead grab the reference to the original ndarray object.
        if (outarr is not None and outarr.shape == ()
            and (context is not None and isinstance(context[0], np.ufunc))):
            r = outarr[()] # if ufunc output is scalar, return it
        else:
            if hasattr(np.ndarray, "__acornext__"):
                r = np.ndarray.__acornext__.__array_wrap__(self, outarr, context)
            else:# pragma: no cover
                r = np.ndarray.__array_wrap__(self, outarr, context)
            
        if isinstance(context, tuple):
            post(fqdn, "numpy", r, entry, bound, ekey, *context[1])

        return r
