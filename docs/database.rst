Notebook Database Documentation
===============================

The `acorn` notebook database is saved as a JSON-serialized dictionary, which we
call a "database". A more accurate name would be a key-value store. The database
has the following attributes:

- **entities**: these are method calls or object instantiation logs. The value
  of the attribute is a dictionary with UUID keys (see next point) and values
  having the "entry" format described below.
- **uuids**: uses Universally Unique Identifier (UUID) strings to identify each
  of the objects that are referenced in the *entities* entries. This dictionary
  has UUID keys and values are dictionaries returned by the :doc:`descriptors`.

Entity Entry Format
-------------------

Each entry in the database can either be a method/function call, or a
constructor call to initialize an object. For constructor calls, we log only the
`__new__` methods; the `__init__` methods are automatically called as well, but
they do *not* produce a log in the database. Entries are JSON dictionaries with
the following attributes:

- **args**: is a dictionary. It has an `__` attribute for the *positional*
  arguments, and then additional attributes for each keyword argument.
- **analysis**: if a method call is configured to trigger analysis, this
  attribute will be a dictionary returned by :doc:`analysis` for the specific
  object type.
- **elapsed**: how many ticks elapsed in order to run the method. We create the
  entry *before* calling the method and then update the *elapsed* time once the
  result has returned. For constructors, this includes the time required to call
  `__init__`.
- **start**: time at which the method/constructor call was started.
- **returns**: object representation for the result of the function call (see
  the discussion on object representations below).
- **method**: the FQDN of the method being called. This can be a constructor,
  instance method, static method, class method, function, built-in, etc.
- **error**: if the call to the constructor/function raised an unhandled
  exception, this is the error message of the exception. The exception is still
  raised to the main notebook thread, we just intercept it to create a log.

Short Representations for Objects
---------------------------------

When a new object is detected that hasn't been handled before, it gets passed to
the :func:`~acorn.logging.database.tracker` method, which determines how best to
represent the object.

- For simple object types (scalars), the object is returned.
- For collections in which *every item* is a simple scalar type, the `len`,
  `min` and `max` as well as the `type` of the collection are extracted and
  pretty-printed in a string.
- For collections of non-scalar types, :func:`~acorn.logging.database.tracker`
  is called for each member of the collection.
- If the object has type `type`, then it's name is returned.
- `lambda` functions (have type :class:`LambdaType`) are represented by
  `lambda(args...)`, where the "args" list is extracted from the `__code__`
  special attribute. If the lambda object has a `__fqdn__` special attribute, it
  is used instead.
- For objects of type :class:`FunctionType` or :class:`MethodType`, the
  `__name__` attribute is returned.
- `numpy.ufunc` instances have their FQDN returned.
- In all other cases, a :class:`acorn.logging.database.Instance` object is
  initialized with the object. It is then represented by a :func:`uuid.uuid4`
  value and its description is handled by :doc:`descriptors`.

Database Naming Conventions: Projects and Tasks
-----------------------------------------------

`acorn` exposes a method :func:`acorn.set_task` that sets a project and task
name for a live session. These values can be changed during a session to work on
a different database. The JSON file name is `project.task.json` and gets stored
in the database directory specified by the :doc:`configuration`. The
database can also be set to be not writeable, in which case the entries are just
logged in-memory. This is useful for unit-testing and debugging.

API Documentation
-----------------

.. automodule:: acorn.logging.database
   :synopsis: Methods and classes for logging database entities and objects.
   :members:
