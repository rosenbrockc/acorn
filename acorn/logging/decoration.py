"""Methods for dynamically adding decorators to all the methods and
classes within a module.
"""
from database import tracker
def isbound(method):
    """Returns True if the method is bounded (i.e., does not require a
    class instance to run.
    """
    return method.im_self is not None

def logger(func):
    def wrapper(*args, **kwargs):
        #parse the arguments and create a string representation
        args = {"__": []}
        for item in argl:
            instance = tracker(item)
            if instance is not None:
                args["__"].append(instance.uuid)
            else:
                args["__"].append(str(item))
                
        for key,item in argd.items():
            args.append('%s=%s' % (key,str(item)))
        argstr = ','.join(args)   
        print >> log,"%s%s.%s(%s) " % (indStr*indent,str(self),methodname,argstr)
        indent += 1
        # do the actual method call
        returnval = getattr(self,'_H_%s' % methodname)(*argl,**argd)
        indent -= 1
        print >> log,'%s:'% (indStr*indent), str(returnval)
        return returnval

        print "before",func.func_name
        print args
        print kwargs
        result = func(*args, **kwargs)
        print "after",func.func_name
        return result
    return wrapper
  
import inspect
def _list_methods(entity):
    """Lists all the methods or functions within the specified entity.
    
    Args:
        entity (type): the type description of the module or class to grab
          methods and functions from.
    """
    methods = []
    for (n, f) in inspect.getmembers(entity):
        if n[0] == '_':
            continue
        if inspect.ismethod(f) or inspect.isfunction(f):
            methods.append((n, f))
        elif inspect.isclass(f):
            methods.extend(_list_methods(f))
        elif inspect.ismodule(f):
            methods.extend(_list_methods(f))
        
    return methods

