"""Methods and classes for creating a JSON database from a tree of
calls to methods with various objects passed as arguments.
"""
#TODO: oids seem to be saving okay; we need to write them to the JSON database,
#but only if they are relevant (i.e., some method calls later refer to them).
from uuid import uuid4
from acorn import msg
oids = {}
"""dict: keys are python :meth:`id` values, values are the :class:`Instance`
class instances from which JSON database can be constructed.
"""
uuids = {}
"""dict: keys are the :class:`UUID` string values; values are :class:`Instance`
class instances (i.e., same values as :data:`oids`, but keyed by `uuid`.
"""
dbs = {}
"""dict: keys are tuple (project, task), values are the databases for the
specified project and task.
"""

_project = "default"
"""str: currently active *project* name under which all logging is being saved.
"""
_task = "default"
"""str: currently active *task* name under which all logging is being saved.
"""
_writable = True
"""bool: when True, calling :meth:`acorn.logging.database.record` will
eventually result in an entry being saved to disk; otherwise, records are
organized in memory, but the disk write is disabled.

"""

def set_task(project, task):
    """Sets the active project and task. All subsequent logging will be saved to
    the database with that project and task.

    Args:
        project (str): active project name; a project can have multiple tasks.
        task (str): active task name. Logging is separated at the project and task
          level.
    """
    global _project, _task
    _project = project
    _task = task    

def set_writable(writable):
    """Sets whether the database is being written to disk, or just organized in
    memory.

    Args: 

        writable (bool): when True, calling :meth:`acorn.database.record` will
          eventually result in an entry being saved to disk; otherwise, records are
          organized in memory, but the disk write is disabled.
    """
    global _writable
    _writable = writable

def tracker(obj):
    """Returns the Instance of the specified object if it is one that
    we track by default.

    Args:
        obj (object): any python object passed as an argument to a method.

    Returns:
        Instance: if the object is trackable, the Instance instance of
          that object; else None.
    """
    import types as typ
    import numpy as anp
    global oids, uuids
    untracked = (basestring, int, long, float, complex, tuple)
    semitrack = (list, dict, set)
    
    if isinstance(obj, semitrack):
        if len(obj) > 0:
            semiform = "{0} len={1:d} min={2} max={3}"
            return semiform.format(type(obj), len(obj), min(obj), max(obj))
        else:
            semiform = "{0} len={1:d}"
            return semiform.format(type(obj), len(obj))
    elif type(obj) is type:
        return obj.__name__
    elif type(obj) is typ.LambdaType:
        return "lambda ({})".format(', '.join(obj.func_code.co_varnames))
    elif type(obj) in [typ.FunctionType, typ.MethodType]:
        return obj.__name__
    elif type(obj) is anp.ufunc:
        return "numpy.{}".format(obj.__name__)
    elif not isinstance(obj, untracked):
        oid = id(obj)
        if oid in oids:
            result = oids[oid]
        else:
            result = Instance(oid, obj)
            oids[oid] = result
            uuids[result.uuid] = result
        return result
    else:
        return None

def _dbdir():
    """Returns the path to the directory where acorn DBs are stored.
    """
    from acorn.config import settings
    config = settings("acorn")
    if (config.has_section("database") and
        config.has_option("database", "folder")):
        from os import mkdir, path
        dbdir = path.abspath(path.expanduser(config.get("database", "folder")))
        if not path.isdir(dbdir):
            mkdir(dbdir)
        return dbdir
    else:
        raise ValueError("The folder to save DBs in must be configured"
                         "  in 'acorn.cfg'")

def record(ekey, entry):
    """Records the specified entry to the key-value store under the specified
    entity key.

    Args:
    ekey (str): fqdn/uuid of the method/object to store the entry for.
    entry (dict): attributes and values gleaned from the execution.
    """
    global _project, _task, dbs
    # The task database is encapsulated in a class for easier serialization to
    # JSON. Get the DB for the (project, task) combination.
    dbkey = (_project, _task)
    if dbkey in dbs:
        taskdb = dbs[dbkey]
    else:
        taskdb = TaskDB()
        dbs[dbkey] = taskdb
    
    taskdb.record(ekey, entry)
    # The task database save method makes sure that we only save as often as
    # specified in the configuration file.
    taskdb.save()
    
class TaskDB(object):
    """Represents the database for a single task.

    Attributes:
        entities (dict): keys are entity ids (fqdn or uuid); values are a list of
          entries generated for that entity during this task.
        uuids (dict): keys are `uuid` values for class instances; values are
          dicts with attributes describing the class instance's origin.
        dbpath (str): full path to the database JSON file for this task
          database.
        lastsave (float): timestamp since the last time the DB was saved.
    """
    def __init__(self, dbdir=None):      
        self.entities = {}
        self.uuids = {}
        if dbdir is None:
            dbdir = _dbdir()

        from os import path
        global _project, _task
        if _project == "default" and _task == "default":
            msg.warn("The project and task are using default values. "
                     "Use :meth:`acorn.set_task` to change them.")
        self.dbpath = path.join(dbdir, "{}.{}.json".format(_project, _task))
        
        self.lastsave = None
        self.load()

    def _log_uuid(self, uuid):
        """Logs the object with the specified `uuid` to `self.uuids` if
        possible.

        Args:
            uuid (str): string value of :meth:`uuid.uuid4` value for the
              object.
        """
        global uuids
        #We only need to try and describe an object once; if it is already in
        #our database, then just move along.
        if uuid not in self.uuids and uuid in uuids:
            self.uuids[uuid] = uuids[uuid].describe()
        
    def record(self, ekey, entry):
        """Records the specified entry to the key-value store under the specified
        entity key.

        Args:
        ekey (str): fqdn/uuid of the method/object to store the entry for.
        entry (dict): attributes and values gleaned from the execution.
        """
        if ekey in self.entities:
            self.entities[ekey].append(entry)
        else:
            self.entities[ekey] = [entry]

        #We also need to make sure we have uuids and origin information stored
        #for any uuids present in the parameter string.
        if entry["returns"] is not None:
            uid = entry["returns"]
            self._log_uuid(uid)

        from uuid import UUID
        for larg in entry["args"]["__"]:
            #We use the constructor to determine if the format of the argument
            #is a valid UUID; if it isn't then we catch the error and keep
            #going.
            try:
                uid = UUID(larg)
                self._log_uuid(uid)
            except ValueError:
                #This was obviously not a UUID, we don't need to worry about it,
                #it has a user-readable string instead.
                pass

        #We also need to handle the keyword arguments; these are keyed by name.
        for key, karg in entry["args"].items():
            if key == "__":
                #Skip the positional arguments since we already handled them.
                continue
            try:
                uid = UUID(karg)
                self._log_uuid(uid)
            except ValueError:
                pass            

    def _get_option(self, option, default=None, cast=None):
        """Returns the option value for the specified acorn database option.
        """
        from acorn.config import settings
        config = settings("acorn")
        if (config.has_section("database") and
            config.has_option("database", option)):
            result = config.get("database", option)
            if cast is not None:
                result = cast(result)        
        else:
            result = default

        return result
            
    def load(self):
        """Deserializes the database from disk.
        """
        #We load the database even when it is not configured to be
        #writable. After all, the user may decide part-way through a session to
        #begin writing again, and then we would want a history up to that point
        #to be valid.
        from os import path
        if path.isfile(self.dbpath):
            import json
            with open(self.dbpath) as f:
                jdb = json.load(f)
                self.entities = jdb["entities"]
                self.uuids = jdb["uuids"]
            
    def save(self):
        """Serializes the database file to disk."""
        global _writable
        if not _writable:
            return       

        # Since the DBs can get rather large, we don't want to save them every
        # single time a method is called. Instead, we only save them at the
        # frequency specified in the global settings file.
        from datetime import datetime
        from time import time
        savefreq = self._get_option("savefreq", 2, int)
        
        if self.lastsave is not None:
            delta = (datetime.fromtimestamp(time()) -
                     datetime.fromtimestamp(self.lastsave)) 
            elapsed = int(delta.total_seconds()/60)
        else:
            elapsed = savefreq + 1

        if elapsed > savefreq:
            import json
            try:
                jdb = {"entities": self.entities,
                       "uuids": self.uuids}
                with open(self.dbpath, 'w') as f:
                    json.dump(jdb, f)
            except:
                from acorn.msg import err
                import sys
                err("{}: {}".format(*sys.exc_info()[0:2]))

            self.lastsave = time()
    
class Instance(object):
    """Represents a class instance in the current session which can be
    passed as an argument to method calls, or have unbound methods
    called in it.

    Args:
        pid (int): python memory address (returned by :func:`id`).

    Attributes:
        uuid (str): :meth:`uuid.uuid4` for the object.
        obj: original object instance that this represents.
    """
    def __init__(self, pid, obj):
        self.pid = pid
        self.uuid = str(uuid4())
        self.obj = obj
        
    def describe(self):
        """Returns a dictionary describing the object based on its type.
        """
        result = {}
        #Because we created an Instance object, we already know that this object
        #is not one of the regular built-in types (except, perhaps, for list,
        #dict and set objects that can have their tracking turned on).

        #For objects that are instantiated by the user in __main__, we will
        #already have a paper trail that shows exactly how it was done; but for
        #these, we have to rely on human-specified descriptions.
        from acorn.logging.descriptors import describe
        return describe(self.obj)
        
