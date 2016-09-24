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
        self.atypes = ["function", "classobj", "staticmethod"]
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
            
            if atype == "classobj":
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

    def _decorate(self, atype, n, o):
        """Decorates the specified object for automatic logging with acorn.

        Args:
            atype (str): one of the types specified in :attr:`atypes`.
            varobj: object instance to decorate; no additional type checking is
              performed.
        """
        typemap = {"function": "functions",
                   "classobj": "classes",
                   "staticmethod": "methods"}
        from acorn.logging.decoration import decorate_obj
        try:
            decorate_obj(self.shell.user_ns, n, o, typemap[atype])
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
