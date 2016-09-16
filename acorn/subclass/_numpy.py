"""Module for implementing the difficult case of array sub-classing for
numpy. This is necessary because of the C-extension nature of the numpy package
and complications with array slices etc. See
http://docs.scipy.org/doc/numpy/user/basics.subclassing.html.
"""
import numpy as np
class ndarray(np.ndarray):
    """Sub-class of :class:`numpy.ndarray` so that we can implement logging for
    the instance method and special method calls of array objects.

    """
    def __new__(cls, input_array):
        from acorn.logging.decoration import set_decorating
        set_decorating(True)
        #Call the original, undecorated version of asarray.
        if isinstance(input_array, np.ndarray):
            if hasattr(np.ndarray.view, "__acorn__"):
                obj = np.ndarray.view.__acorn__(input_array, cls)
            else:
                obj = np.ndarray.view(input_array, cls)
        else:
            if hasattr(np.asarray, "__acorn__"):
                obj = np.asarray.__acorn__(input_array).view(cls)
            else:
                obj = np.asarray(input_array).view(cls)
        set_decorating(False)
        
        obj.__acorn__ = np.ndarray
        obj.__doc__ = np.ndarray.__doc__
        return obj

    def __getslice__(self, *items):
        #Unfortunately, we have to implement the slicing here since it does not
        #call any other methods that get decorated. We know that a slice is
        #happening when the type of `self` and `obj` are the same and are equal
        #to acorn.subclass_numpy.ndarray (instead of the regular numpy.ndarray).
        from acorn.logging.decoration import (rt_decorate_pre,
                                              rt_decorate_post,
                                              _fqdn)
        fqdn = "numpy.ndarray.__getslice__"
        entry, bound, ekey = rt_decorate_pre(fqdn, None, 4, *((self,) + items))
        
        # Because we had to subclass numpy.ndarray, the original methods get
        # stuck in an infinite loop (max. recursion depth exceeded errors). So,
        # we instead grab the reference to the original ndarray object.
        r = np.ndarray.__acornext__.__getslice__(self, *items)
        # This method can trick acorn into thinking that it is a bound
        # method. We want it to behave like it's not.
        rt_decorate_post(fqdn, "numpy", r, entry, False, ekey)
        return r        
    
    def __array_finalize__(self, obj):
        if obj is None: return
        self.__acorn__ = getattr(obj, '__acorn__', None)

    def __array_wrap__(self, outarr, context=None):
        if isinstance(context, tuple):
            from acorn.logging.decoration import (rt_decorate_pre,
                                                  rt_decorate_post,
                                                  _fqdn)
            fqdn = _fqdn(context[0], "unknown", False)
            entry, bound, ekey = rt_decorate_pre(fqdn, None, 4, *context[1])

        # Because we had to subclass numpy.ndarray, the original methods get
        # stuck in an infinite loop (max. recursion depth exceeded errors). So,
        # we instead grab the reference to the original ndarray object.
        if (outarr is not None and outarr.shape == ()
            and (context is not None and isinstance(context[0], np.ufunc))):
            r = outarr[()] # if ufunc output is scalar, return it
        else:
            if hasattr(np.ndarray, "__acornext__"):
                r = np.ndarray.__acornext__.__array_wrap__(self, outarr, context)
            else:
                r = np.ndarray.__array_wrap__(self, outarr, context)
            
        if isinstance(context, tuple):
            rt_decorate_post(fqdn, "numpy", r, entry, bound, ekey)

        return r
