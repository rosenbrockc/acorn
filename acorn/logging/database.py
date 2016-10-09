"""Methods and classes for creating a JSON database from a tree of
calls to methods with various objects passed as arguments.
"""
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
"""dict: keys are tuple (project, task), values are the :class:`TaskDB`
instances for the specified project and task.
"""

project = "default"
"""str: currently active *project* name under which all logging is being saved.
"""
task = "default"
"""str: currently active *task* name under which all logging is being saved.
"""
writeable = True
"""bool: when True, calling :meth:`acorn.logging.database.record` will
eventually result in an entry being saved to disk; otherwise, records are
organized in memory, but the disk write is disabled.

"""
dbdir = None
"""str: full path to the directory where the databases are being stored. If this
is overwritten programatically, then the global settings for `acorn` will *not*
be checked.
"""
def set_dbdir(dbdir_):
    """Sets the path to the directory where the JSON files should be
    stored. Calling this method side-steps the configuration settings in the
    `acorn.cfg` global config file.

    Args:
        dbdir_ (str): path to the dbdir; can be relative.
    """
    global dbdir
    dbdir = dbdir_

def list_tasks(target=None):
    """Returns a list of all the projects and tasks available in the `acorn`
    database directory.

    Args:
        target (str): directory to list the projects for. Defaults to the configured
          database directory.    

    Returns:
        dict: keys are project names; values are lists of tasks associated with the
          project.
    """
    from os import getcwd, chdir
    from glob import glob
    original = getcwd()
    if target is None:# pragma: no cover
        target = _dbdir()
        
    chdir(target)
    result = {}
    for filename in glob("*.*.json"):
        project, task = filename.split('.')[0:2]
        if project not in result:
            result[project] = []
        result[project].append(task)

    #Set the working directory back to what it was.
    chdir(original)
        
    return result
    
def set_task(project_, task_):
    """Sets the active project and task. All subsequent logging will be saved to
    the database with that project and task.

    Args:
        project_ (str): active project name; a project can have multiple tasks.
        task_ (str): active task name. Logging is separated at the project and task
          level.
    """
    global project, task
    project = project_
    task = task_
    msg.okay("Set project name to {}.{}".format(project, task), 2)

def set_writeable(writeable_):
    """Sets whether the database is being written to disk, or just organized in
    memory.

    Args: 

        writeable_ (bool): when True, calling :meth:`acorn.database.record` will
          eventually result in an entry being saved to disk; otherwise, records are
          organized in memory, but the disk write is disabled.
    """
    global writeable
    writeable = writeable_

def cleanup():
    """Saves all the open databases to JSON so that the kernel can be shut down
    without losing in-memory collections.
    """
    failed = {}
    success = []
    for dbname, db in dbs.items():
        try:
            #Force the database save, even if the time hasn't elapsed yet.
            db.save(True)
            success.append(dbname)
        except: # pragma: no cover
            import sys, traceback
            xcls, xerr = sys.exc_info()[0:2]
            failed[dbname] = traceback.format_tb(sys.exc_info()[2])

    for sdb in success:
        if writeable:
            msg.okay("Project {0}.{1} saved successfully.".format(*sdb), 0)
    for fdb, tb in failed.items(): # pragma: no cover
        msg.err("Project {1}.{2} save failed:\n{0}".format(tb, *fdb),
                prefix=False)
    
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
    global oids, uuids
    import six
    from inspect import isclass
    untracked = (six.string_types, six.integer_types, float,
                 complex, six.text_type)

    semitrack = (list, dict, set, tuple)
    if six.PY3: # pragma: no cover
        semitrack = semitrack + (range, filter, map)
        
    if (isinstance(obj, semitrack) and
        all([isinstance(t, untracked) for t in obj])):
        if len(obj) > 0:
            semiform = "{0} len={1:d} min={2} max={3}"
            return semiform.format(type(obj), len(obj), min(obj), max(obj))
        else:
            semiform = "{0} len={1:d}"
            return semiform.format(type(obj), len(obj))
    elif isinstance(obj, semitrack):
        #We have to run the tracker on each of the elements in the list, set,
        #dict or tuple; this is necessary so that we can keep track of
        #subsequent calls made with unpacked parts of the tuple.
        result = []
        for o in obj:
            track = tracker(o)
            if isinstance(track, Instance):
                result.append(track.uuid)
            else:
                result.append(track)
        return tuple(result)
    elif isinstance(obj, slice):
        return "slice({}, {}, {})".format(obj.start, obj.stop, obj.step)
    elif type(obj) is type:
        return obj.__name__
    elif type(obj) is typ.LambdaType:
        if hasattr(obj, "__fqdn__"):
            #We need to get the actual fqdn of the object *before* it was
            #decorated.
            return obj.__fqdn__
        else:
            if six.PY2:
                _code = obj.func_code
            else: # pragma: no cover
                _code = obj.__code__
            return "lambda ({})".format(', '.join(_code.co_varnames))
    elif type(obj) in [typ.FunctionType, typ.MethodType]: # pragma: no cover
        return obj.__name__
    elif not isinstance(obj, untracked):
        #For many of the numpy/scipy methods, the result is a tuple of numpy
        #arrays. In that case, we should maintain the tuple structure for
        #descriptive purposes, but still return a tracker.
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
    global dbdir
    from os import mkdir, path, getcwd, chdir
    
    if dbdir is None:
        from acorn.config import settings
        config = settings("acorn")
        if (config.has_section("database") and
            config.has_option("database", "folder")):
            dbdir = config.get("database", "folder")
        else: # pragma: no cover
            raise ValueError("The folder to save DBs in must be configured"
                             "  in 'acorn.cfg'")

    #It is possible to specify the database path relative to the repository
    #root. path.abspath will map it correctly if we are in the root directory.
    from acorn.utility import abspath
    if not path.isabs(dbdir):
        #We want absolute paths to make it easier to port this to other OS.
        dbdir = abspath(dbdir)
        
    if not path.isdir(dbdir): # pragma: no cover
        mkdir(dbdir)
        
    return dbdir

def _json_clean(d):
    """Cleans the specified python `dict` by converting any tuple keys to
    strings so that they can be serialized by JSON.

    Args:
        d (dict): python dictionary to clean up.

    Returns:
        dict: cleaned-up dictionary.
    """
    result = {}
    compkeys = {}
    for k, v in d.items():
        if not isinstance(k, tuple):
            result[k] = v
        else:
            #v is a list of entries for instance methods/constructors on the
            #UUID of the key. Instead of using the composite tuple keys, we
            #switch them for a string using the 
            key = "c.{}".format(id(k))
            result[key] = v
            compkeys[key] = k

    return (result, compkeys)

def record(ekey, entry):
    """Records the specified entry to the key-value store under the specified
    entity key.

    Args:
    ekey (str): fqdn/uuid of the method/object to store the entry for.
    entry (dict): attributes and values gleaned from the execution.
    """
    global dbs
    # The task database is encapsulated in a class for easier serialization to
    # JSON. Get the DB for the (project, task) combination.
    dbkey = (project, task)
    if dbkey in dbs:
        taskdb = dbs[dbkey]
    else:
        taskdb = TaskDB()
        dbs[dbkey] = taskdb
        msg.okay("Initialized JSON database for {}.{}".format(*dbkey), 2)
    
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
        if project == "default" and task == "default": # pragma: no cover
            msg.warn("The project and task are using default values. "
                     "Use :meth:`acorn.set_task` to change them.")
        self.dbpath = path.join(dbdir, "{}.{}.json".format(project, task))
        
        self.lastsave = None
        self.load()

    def _log_uuid(self, uuid):
        """Logs the object with the specified `uuid` to `self.uuids` if
        possible.

        Args:
            uuid (str): string value of :meth:`uuid.uuid4` value for the
              object.
        """
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
        from uuid import UUID
        uid = None
        if entry["r"] is not None:
            uid = entry["r"]
        elif isinstance(ekey, str):
            #For many methods we don't duplicate the UUID in the returns part
            #because it wastes space. In those cases, the ekey is a UUID.
            try:
                uid = str(UUID(ekey))
            except ValueError: # pragma: no cover
                pass

        if uid is not None and isinstance(uid, str):
            self._log_uuid(uid)

        for larg in entry["a"]["_"]:
            #We use the constructor to determine if the format of the argument
            #is a valid UUID; if it isn't then we catch the error and keep
            #going.
            if not isinstance(larg, str):
                continue
            
            try:
                uid = str(UUID(larg))
                self._log_uuid(uid)
            except ValueError:
                #This was obviously not a UUID, we don't need to worry about it,
                #it has a user-readable string instead.
                pass

        #We also need to handle the keyword arguments; these are keyed by name.
        for key, karg in entry["a"].items():
            if key == "_" or not isinstance(karg, str):
                #Skip the positional arguments since we already handled them.
                continue
            try:
                uid = str(UUID(karg))
                self._log_uuid(uid)
            except ValueError:
                pass            

    @staticmethod
    def get_option(option, default=None, cast=None):
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
            
    def save(self, force=False):
        """Serializes the database file to disk.

        Args:
            force (bool): when True, the elapsed time since last save is ignored
                and the database is saved anyway (subject to global
                :data:`writeable` setting).
        """
        from time import time

        # Since the DBs can get rather large, we don't want to save them every
        # single time a method is called. Instead, we only save them at the
        # frequency specified in the global settings file.
        from datetime import datetime
        savefreq = TaskDB.get_option("savefreq", 2, int)
        
        if self.lastsave is not None:
            delta = (datetime.fromtimestamp(time()) -
                     datetime.fromtimestamp(self.lastsave)) 
            elapsed = int(delta.total_seconds()/60)
        else:
            elapsed = savefreq + 1

        if elapsed > savefreq or force:
            if not writeable:
                #We still overwrite the lastsave value so that this message doesn't
                #keep getting output for every :meth:`record` call.
                self.lastsave = time()
                msg.std("Skipping database write to disk by setting.", 2)
                return

            import json
            try:
                entities, compkeys = _json_clean(self.entities)
                jdb = {"entities": entities,
                       "compkeys": compkeys,
                       "uuids": self.uuids}
                with open(self.dbpath, 'w') as f:
                    json.dump(jdb, f)
            except: # pragma: no cover
                from acorn.msg import err
                import sys
                raise
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
