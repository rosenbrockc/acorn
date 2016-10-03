"""Methods for interacting with an ipython notebook or shell so that new
functions defined interactively are also logged by acorn.
"""
from acorn import msg
class InteractiveDecorator(object):
    """Class for maintaining the state of functions declared interactively in
    the ipython notebook. Exposes callback functions for pre- and post- cell
    execution in ipython.

    Args:
        ip (IPython.core.interactiveshell.InteractiveShell): ipython shell instance
          for interacting with the shell variables.

    Attributes:
        atypes (list): names of types that are tracked for decoration by acorn.
        entities (dict): keys are object types specified in :attr:`atypes`; values
          are `dict` of variable names and values in the local user namespace.
    """
    def __init__(self, ip):
        self.shell = ip
        self.atypes = ["function", "classobj", "staticmethod", "type"]
        self.entities = {k: {} for k in self.atypes}

    def _get_decoratables(self, atype):
        """Returns a list of the objects that need to be decorated in the
        current user namespace based on their type.

        Args:
            atype (str): one of the values in :attr:`atypes`. Specifies the type of
              object to search.
        """
        result = []
        defmsg = "Skipping {}; not decoratable or already decorated."
        for varname in self.shell.run_line_magic("who_ls", atype):
            varobj = self.shell.user_ns.get(varname, None)
            decorate = False
            
            if varobj is None: # Nothing useful can be done.
                continue
            
            if atype in ["classobj", "type"]:
                #Classes are only relevant if they have no __file__
                #attribute; all other classes should be decorated by the
                #full acorn machinery.
                if (not hasattr(varobj, "__acorn__") and
                    hasattr(varobj, "__module__") and
                    varobj.__module__ == "__main__" and
                    not hasattr(varobj, "__file__")):
                    decorate = True
                else:
                    msg.std(defmsg.format(varname), 3)
                    
            elif atype in ["function", "staticmethod"]:
                # %who_ls will only return functions from the *user*
                # namespace, so we don't have a lot to worry about here.
                func = None
                if atype == "staticmethod" and hasattr(varobj, "__func__"):
                    func = varobj.__func__
                elif atype == "function":
                    func = varobj

                if (func is not None and
                    not hasattr(func, "__acorn__") and
                    hasattr(func, "__code__") and
                    "<ipython-input" in func.__code__.co_filename):
                    decorate = True
                else:
                    msg.std(defmsg.format(varname), 3)
                    
            if decorate:
                self.entities[atype][varname] = varobj
                result.append((varname, varobj))
                
        return result        

    def _logdef(self, n, o, otype):
        """Logs the definition of the object that was just auto-decorated inside
        the `ipython` notebook.
        """
        import re
        try:
            #The latest input cell will be the one that this got executed
            #from. TODO: actually, if acorn got imported after the fact, then
            #the import would have caused all the undecorated functions to be
            #decorated as soon as acorn imported. I suppose we just won't have
            #any code for that case.
            if otype == "classes":
                cellno = max([int(k[2:]) for k in self.shell.user_ns.keys()
                              if re.match("_i\d+", k)])
            elif otype == "functions":
                cellno = int(o.__code__.co_filename.strip("<>").split('-')[2])
        except:
            #This must not have been an ipython notebook declaration, so we
            #don't store the code.
            cellno = None
            pass
        
        code = ""
        if cellno is not None:
            cellstr = "_i{0:d}".format(cellno)
            if cellstr in self.shell.user_ns:
                cellcode = self.shell.user_ns[cellstr]
                import ast
                astm = ast.parse(cellcode)
                ab = astm.body
                parts = {ab[i].name: (ab[i].lineno, None if i+1 >= len(ab)
                                      else ab[i+1].lineno) 
                         for i, d in enumerate(ab)}
                if n in parts:
                    celllines = cellcode.split('\n')
                    start, end = parts[n]
                    if end is not None:
                        code = celllines[start-1:end-1]
                    else:
                        code = celllines[start-1:]

        #Now, we actually create the entry. Since the execution for function
        #definitions is almost instantaneous, we just log the pre and post
        #events at the same time.
        from time import time
        from acorn.logging.database import record
        from acorn.logging.decoration import _tracker_str
        entry = {
            "m": "__main__.{}".format(n),
            "a": {"_": []},
            "s": time(),
            "r": None,
            "c": code,
        }
        from acorn import msg
        record("def", entry)
        msg.info(entry, 1)
        
    def _decorate(self, atype, n, o):
        """Decorates the specified object for automatic logging with acorn.

        Args:
            atype (str): one of the types specified in :attr:`atypes`.
            varobj: object instance to decorate; no additional type checking is
              performed.
        """
        typemap = {"function": "functions",
                   "classobj": "classes",
                   "staticmethod": "methods",
                   "type": "classes"}
        from acorn.logging.decoration import decorate_obj
        try:
            otype = typemap[atype]
            decorate_obj(self.shell.user_ns, n, o, otype)
            #Also create a log in the database for this execution; this allows a
            #user to track the changes they make in prototyping function and
            #class definitions.
            self._logdef(n, o, otype)
            msg.okay("Auto-decorated {}: {}.".format(n, o))
        except:
            msg.err("Error auto-decorating {}: {}.".format(n, o))
            raise
            
    def post_run_cell(self):
        #We just want to detect any new, decoratable objects that haven't been
        #decorated yet.
        decorlist = {k: [] for k in self.atypes}
        for atype in self.atypes:
            for n, o in self._get_decoratables(atype):
                self._decorate(atype, n, o)

def load_ipython_extension(ip):
    """Loads the interacting decorator that ships with `acorn` into the ipython
    interactive shell.

    Args:
        ip (IPython.core.interactiveshell.InteractiveShell): ipython shell instance
          for interacting with the shell variables.
    """
    decor = InteractiveDecorator(ip)
    ip.events.register('post_run_cell', decor.post_run_cell)
