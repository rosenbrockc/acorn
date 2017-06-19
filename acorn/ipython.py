"""Methods for interacting with an ipython notebook or shell so that new
functions defined interactively are also logged by acorn.
"""
from acorn import msg
from IPython.core.formatters import PNGFormatter, JPEGFormatter

thumb_uuid = None
"""str: uuid of the image file that was most recently generated from a plot. The
post-execution hook of the cell checks this variable to see if an image should
be associated with the cell's output.
"""
inspectors = ["isclass", "isfunction", "ismethod", "ismodule"]
"""list: of functions in :mod:`inspect` that will be *ignored* by the
automatic variable tracking after cell execution.
"""

class AcornPNGFormatter(PNGFormatter):
    """Replaces the default display formatter for the ipython notebooks that
    handles PNG images. This allows thumbnails of plots to be generated as part
    of the notebook flow.
    """
    def __call__(self, obj):
        global thumb_uuid
        result = super(PNGFormatter, self).__call__(obj)
        if result is not None:
            #We have a PNG image that could be written to file now. First, we
            #create the image file, then we save the image UUID to the global
            #variable so that the database machinery can grab it.
            from acorn.logging.database import save_image
            uuid = save_image(result, "png")

            if thumb_uuid is None:
                thumb_uuid = []
            thumb_uuid.append(uuid)
            
        return result

class AcornJPEGFormatter(JPEGFormatter):
    """Replaces the default display formatter for the ipython notebooks that
    handles JPEG images. This allows thumbnails of plots to be generated as part
    of the notebook flow.
    """
    def __call__(self, obj):
        global thumb_uuid
        result = super(JPEGFormatter, self).__call__(obj)
        if result is not None:
            #We have a PNG image that could be written to file now. First, we
            #create the image file, then we save the image UUID to the global
            #variable so that the database machinery can grab it.
            from acorn.logging.database import save_image
            uuid = save_image(result, "jpeg")

            if thumb_uuid is None:
                thumb_uuid = []
            thumb_uuid.append(uuid)
            
        return result

from IPython.core.history import HistoryManager
class AcornHistoryManager(HistoryManager):
    """Sub-class for overriding the input storing during cell execution to allow
    acorn to detect loops and other problematic code *before* it
    executes. Necessary because the ipython hooks that we can register functions
    to *don't* have access to the raw cell code that we need to parse.

    Args:
        existing (IPython.core.HistoryManager): existing instance that possible
          has some history entries already. This instance's __dict__ overwrites
          the new sub-class instance's one.
        decorator (InteractiveDecorator): acorn ipython decorator for
          intercepting code execution and logging behavior.
    """
    def __init__(self, existing, decorator):
        super(AcornHistoryManager, self).__init__(shell=existing.shell,
                                                  parent=existing.parent)
        self.old = existing
        self.decorator = decorator

        #These are the history related items that we want to copy over. We tried
        #a simple __dict__.update() but it screwed up the pointers etc. and the
        #history didn't work properly. This way, we preserve the important
        #functionality.
        keep = ["input_hist_parsed", "input_hist_raw", "dir_hist",
                "output_hist", "output_hist_reprs", "session_number",
                "session_number", "db_input_cache", "db_output_cache",
                "_i00", "_i", "_ii", "_iii"]
        for k in keep:
            setattr(self, k, getattr(existing, k))

    # def __getattr__(self, attr):
    #     if hasattr(self.old, attr):
    #         return getattr(self.old, attr)
            
    def store_inputs(self, line_num, source, source_raw=None):
        """Store source and raw input in history and create input cache
        variables ``_i*``.

        Args:
            line_num (int): The prompt number of this input.
            source (str): Python input.
            source_raw (str): If given, this is the raw input without any
              IPython transformations applied to it.  If not given, ``source``
              is used.
        """
        self.old.store_inputs(line_num, source, source_raw)
        #Now that the input has been stored correctly, intercept the
        #pre-execution and create logs accordingly.
        self.decorator.pre_run_cell(line_num, source)
    
class InteractiveDecorator(object):
    """Class for maintaining the state of functions declared interactively in
    the ipython notebook. Exposes callback functions for pre- and post- cell
    execution in ipython.

    Args:
        ip (IPython.core.interactiveshell.InteractiveShell): ipython shell instance
          for interacting with the shell variables.

    Attributes:
        shell: (IPython.core.interactiveshell.InteractiveShell): ipython shell
          instance for interacting with the shell variables.
        atypes (list): names of types that are tracked for decoration by acorn.
        entities (dict): keys are object types specified in :attr:`atypes`; values
          are `dict` of variable names and values in the local user namespace.
        who (dict): keys are user variable names; values are the `id()` memory
          addresses. Used to keep track of variables whose values change between
          executions of cells in ipython.
        pre (dict): pre-execution database entry that will be updated with
          results after execution has been performed by ipython.
        cellids (dict): keys are *original* cell ids in the ipython notebook cell
          that was intercepted because it contained loops or other problematic
          code (from the viewpoint of the acorn database). Values are the
          *latest* version of the code. When a loop intercepted cell is run
          again, we search for a cell with most (at least 50%) overlap in
          contents and then treat that as a re-execute, after which the contents
          are overwritten by the most recent version.
        cellid (int): id of the *most recently* loop-intercepted cell in the
          ipython notebook.
    """
    def __init__(self, ip):
        self.shell = ip
        self.atypes = ["function", "classobj", "staticmethod", "type"]
        self.entities = {k: {} for k in self.atypes}
        self.who = {}
        self.pre = None
        self.cellids = {}
        self.cellid = None

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
        entry = {
            "m": "def",
            "a": None,
            "s": time(),
            "r": None,
            "c": code,
        }
        from acorn import msg
        record("__main__.{}".format(n), entry, diff=True)
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

    def _find_cellid(self, code):
        """Determines the most similar cell (if any) to the specified code. It
        must have at least 50% overlap ratio and have been a loop-intercepted
        cell previously.

        Args:
            code (str): contents of the code cell that were executed.
        """
        from difflib import SequenceMatcher
        maxvalue = 0.
        maxid = None
        
        for cellid, c in self.cellids.items():
            matcher = SequenceMatcher(a=c, b=code)
            ratio = matcher.quick_ratio()
            if ratio > maxvalue and ratio > 0.5:
                maxid, maxvalue = cellid, ratio

        return maxid

    def _log_images(self):
        """Creates database logs for all the image file names in the global
        variable :data:`thumb_uuid`.
        """
        from time import time
        from acorn.logging.database import record        
        entry = {
            "m": "plot",
            "a": None,
            "s": time(),
            "r": thumb_uuid,
        }
        
        #See if we can match the executed cell's code up with one that we
        #intercepted in the past..
        code = self.shell.user_ns.get("i_{0:d}".format(self.cellid))
        cellid = self._find_cellid(code)
        if cellid is None:
            cellid = self.cellid
        #Store the contents of the cell so they are up to date for next time.
        self.cellids[cellid] = code

        from acorn import msg
        record("__main__.{}".format(cellid), entry)
        msg.info(entry, 1)
    
    def post_run_cell(self):
        """Runs after the user-entered code in a cell has been executed. It
        detects any new, decoratable objects that haven't been decorated yet and
        then decorates them.
        """
        #We just want to detect any new, decoratable objects that haven't been
        #decorated yet.
        decorlist = {k: [] for k in self.atypes}
        for atype in self.atypes:
            for n, o in self._get_decoratables(atype):
                self._decorate(atype, n, o)

        #Next, check whether we have an outstanding "loop intercept" that we
        #"wrapped" with respect to acorn by enabling streamlining.
        if self.pre is not None:
            #Re-enable the acorn logging systems so that it gets back to normal.
            from acorn.logging.decoration import set_streamlining
            set_streamlining(False)

            from acorn import msg
            from acorn.logging.database import record
            from time import time

            #Determine the elapsed time for the execution of the entire cell.
            entry = self.pre
            entry["e"] = time() - entry["s"]
            #See if we can match the executed cell's code up with one that we
            #intercepted in the past..
            cellid = self._find_cellid(entry["c"])
            if cellid is None:
                cellid = self.cellid

            #Store the contents of the cell *before* they get overwritten by a
            #diff.
            self.cellids[cellid] = entry["c"]
                        
            record("__main__.{0:d}".format(cellid), entry, diff=True)
            msg.info(entry, 1)

            self.pre = None

        #Finally, check whether any new variables have shown up, or have had
        #their values changed.
        from acorn.logging.database import tracker, active_db, Instance
        varchange = self._var_changes()
        taskdb = active_db()
        for n, o in varchange:
            otrack = tracker(o)
            if isinstance(otrack, Instance):
                taskdb.log_uuid(otrack.uuid)

        global thumb_uuid
        if thumb_uuid is not None:
            self._log_images()
            #Reset the image tracker list so that we don't save these images
            #again next cell execution.
            thumb_uuid = None
            
        self.cellid = None
        
    def _var_changes(self):
        """Determines the list of variables whose values have changed since the
        last cell execution.
        """       
        result = []
        variables = self.shell.run_line_magic("who_ls", "")
        if variables is None:
            return result

        import inspect
        for varname in variables:
            varobj = self.shell.user_ns.get(varname, None)
            if varobj is None:
                continue

            #We need to make sure that the objects have types that make
            #sense. We auto-decorate all classes and functions; also modules and
            #other programming constructs are not variables.
            keep = False
            for ifunc in inspectors:
                if getattr(inspect, ifunc)(varobj):
                    break
            else:
                keep = True    

            if keep:
                whoid = id(varobj)
                if varname not in self.who or self.who[varname] != whoid:
                    result.append((varname, varobj))
                    self.who[varname] = whoid
        return result
                
    def pre_run_cell(self, cellno, code):
        """Executes before the user-entered code in `ipython` is run. This
        intercepts loops and other problematic code that would produce lots of
        database entries and streamlines it to produce only a single entry.

        Args:
            cellno (int): the cell number that is about to be executed.
            code (str): python source code that is about to be executed.
        """
        #First, we look for loops and list/dict comprehensions in the code. Find
        #the id of the latest cell that was executed.
        self.cellid = cellno
        
        #If there is a loop somewhere in the code, it could generate millions of
        #database entries and make the notebook unusable.
        import ast
        if findloop(ast.parse(code)):
            #Disable the acorn logging systems so that we don't pollute the
            #database.
            from acorn.logging.decoration import set_streamlining
            set_streamlining(True)

            #Create the pre-execute entry for the database.
            from time import time
            self.pre = {
                "m": "loop",
                "a": None,
                "s": time(),
                "r": None,
                "c": code,
            }

def findloop(m):
    """Determines if the specified member of `_ast` contains any for or while loops
    in its body definition.
    """
    from _ast import For, While, FunctionDef, ClassDef, ListComp    
    from _ast import DictComp
    if isinstance(m, (FunctionDef, ClassDef)):
        return False
    elif isinstance(m, (For, While, ListComp, DictComp)):
        return True
    elif hasattr(m, "value"):
        return findloop(m.value)
    elif hasattr(m, "__iter__"):
        for sm in m:
            present = findloop(sm)
            if present:
                break
        else:
            present = False
        return present
    elif hasattr(m, "body") or hasattr(m, "orelse"):
        body = hasattr(m, "body") and findloop(m.body)
        orelse = hasattr(m, "orelse") and findloop(m.orelse)
        return body or orelse
    else:
        return False
    
_cellid_map = {}
"""dict: keys are string UUIDs from the ipython notebook for the *current*
session; values are the `ekey` from the acorn database of the *previous*
session. When a cell is rendered, if its `ekey` doesn't exist in the database,
we first try and decide quickly if it is similar to a cell from a previous
session. If it is, then we use UUID instead.
"""
    
def record_markdown(text, cellid):
    """Records the specified markdown text to the acorn database.

    Args:
        text (str): the *raw* markdown text entered into the cell in the ipython
          notebook.
    """
    from acorn.logging.database import record
    from time import time
    ekey = "nb-{}".format(cellid)
    
    global _cellid_map
    if cellid not in _cellid_map:
        from acorn.logging.database import active_db
        from difflib import SequenceMatcher
        from acorn.logging.diff import cascade
        taskdb = active_db()
        
        if ekey not in taskdb.entities:
            #Compute a new ekey if possible with the most similar markdown cell
            #in the database.
            possible = [k for k in taskdb.entities if k[0:3] == "nb-"]
            maxkey, maxvalue = None, 0.
            for pkey in possible:
                sequence = [e["c"] for e in taskdb.entities[pkey]]
                state = ''.join(cascade(sequence))
                matcher = SequenceMatcher(a=state, b=text)
                ratio = matcher.quick_ratio()
                if ratio > maxvalue and ratio > 0.5:
                    maxkey, maxvalue = pkey, ratio

            #We expect the similarity to be at least 0.5; otherwise we decide
            #that it is a new cell.
            if maxkey is not None:
                ekey = pkey
                            
        _cellid_map[cellid] = ekey
        
    ekey = _cellid_map[cellid]        
    entry = {
        "m": "md",
        "a": None,
        "s": time(),
        "r": None,
        "c": text,
    }
    record(ekey, entry, diff=True)

def load_ipython_extension(ip):
    """Loads the interacting decorator that ships with `acorn` into the ipython
    interactive shell.

    Args:
        ip (IPython.core.interactiveshell.InteractiveShell): ipython shell instance
          for interacting with the shell variables.
    """
    decor = InteractiveDecorator(ip)
    ip.events.register('post_run_cell', decor.post_run_cell)

    #Unfortunately, the built-in "pre-execute" and "pre-run" methods are
    #triggered *before* the input from the cell has been stored to
    #history. Thus, we don't have access to the actual code that is about to be
    #executed. Instead, we use our own :class:`HistoryManager` that overrides
    #the :meth:`store_inputs` so we can handle the loop detection.
    newhist = AcornHistoryManager(ip.history_manager, decor)
    ip.history_manager = newhist
