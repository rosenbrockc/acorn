"""Methods and classes for creating a JSON database from a tree of
calls to methods with various objects passed as arguments.
"""
from uuid import uuid4
oids = {}
"""dict: keys are python :meth:`id` values, values are the Instance
class instances from which JSON database can be constructed.
"""

dbs = {}
"""dict: keys are tuple (project, task), values are the databases for the
specified project and task.
"""

_project = None
"""str: currently active *project* name under which all logging is being saved.
"""
_task = None
"""str: currently active *task* name under which all logging is being saved.
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

def tracker(obj):
    """Returns the Instance of the specified object if it is one that
    we track by default.

    Args:
    obj (object): any python object passed as an argument to a method.

    Returns:
    Instance: if the object is trackable, the Instance instance of
    that object; else None.
    """
    global oids
    untracked = (basestring, int, long, float, complex, tuple, list, dict, set)
    if not isinstance(obj, untracked):
        oid = id(obj)
        if oid in oids:
            result = oids[oid]
        else:
            result = Instance(obj)
            oids[oid] = result
        return result
    else:
        return None

def _dbdir():
    """Returns the path to the directory where acorn DBs are stored.
    """
    from acorn.utility import settings
    config = settings("acorn")
    if config.has_section("database"):
        dbdir = config.get("database", "folder")
        from os import mkdir, path
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
        dbpath (str): full path to the database JSON file for this task
          database.
        lastsave (float): timestamp since the last time the DB was saved.
    """
    def __init__(self, dbdir):
        from os import path
        global _package, _task
        
        self.entities = {}
        self.dbpath = path.join(dbdir, "{}.{}.json".format(_package, _task))
        self.lastsave = None
        self.load()

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

    def load(self):
        """Deserializes the database from disk.
        """
        from os import path
        if path.isfile(self.dbppath):
            with open(self.dbpath) as f:
                self.entities = json.load(f)
            
    def save(self):
        """Serializes the database file to disk."""
        # Since the DBs can get rather large, we don't want to save them every
        # single time a method is called. Instead, we only save them at the
        # frequency specified in the global settings file.
        from acorn.utility import settings
        from datetime import datetime
        from time import time
        
        config = settings("acorn")
        if config.has_section("database"):
            savefreq = config.get("database", "savefreq", 2)
        else:
            savefreq = 2
        delta = (datetime.fromtimestamp(time()) -
                 datetime.fromtimestamp(self.lastsave)) 
        elapsed = int(delta.total_seconds()/60)

        if elapsed > savefreq:
            import json
            try:
                with open(self.dbpath, 'w') as f:
                    json.dump(self.entities, f)
            except:
                from acorn.msg import err
                import sys
                err(sys.exc_info()[0])

            self.lastsave = time()
    
class Instance(object):
    """Represents a class instance in the current session which can be
    passed as an argument to method calls, or have unbound methods
    called in it.

    Args:
    pid (int): python memory address (returned by :meth:`id`).
    """
    def __init__(self, pid):
        self.pid = pid
        self.uuid = uuid4()
