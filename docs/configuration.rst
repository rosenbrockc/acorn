Global and Package Configuration in ACORN
=========================================

Default configuration files for the following packages ship with the the python
package as package data. If the user doesn't set their own package directory up,
then these will be used.

- acorn (global configuration file)
- numpy
- scipy
- pandas
- sklearn
- matplotlib

To override these configuration files, the user should create a directory called
`.acorn` in their user home directory. If that directory exists, then *only*
package files in that folder will be used.

JSON templates for the object descriptors (see :doc:`descriptors`) also ship for
some of the packages. These can be fine-tuned by the user as well by including a
`package.json` file in `.acorn`.

Configuration Structure
-----------------------

There are several sets of configuration domains in `acorn`:

1. Package configuration. For each package, the logging, tracking and decoration
   behavior can be changed to fine-tune `acorn` behavior for a specific user's
   workflow.
2. Global configuration for `acorn`; this changes the behavior of `acorn` for
   *all* packages, databases, etc.
3. Descriptor configuration. For each object type (across all packages), the way
   `acorn` describes the object can be configured finely. The syntax for this
   kind of configuration is described in :doc:`descriptors`.

Package Configuration
---------------------

Each package can have the following options sections configured:

- **[tracking]**: exposes options for deciding which objects get decorated.
- **[timing]**: exposes options for deciding which method calls should have an
  "elapsed time" stored in the database. By default, all method calls are
  timed.
- **[analysis]**: exposes options for deciding which method calls should have
  their results analyzed by an additional function. All analysis is performed by
  the :doc:`analysis` machinery on a per-object basis (i.e., based on FQDN).
- **[subclass]**: lists objects for which *special* sub-classes are
  available. By default, `acorn` will sub-class any class that cannot be
  decorated using standard machinery. When something special needs to happen,
  this is where the mapping is specified. E.g.,
  `numpy.ndarray=acorn.subclass._numpy.ndarray` specifies that when
  `numpy.ndarray` is encountered during decoration, it should be sub-classed by
  the `acorn` replacement.
- **[callwrap]**: when a method call returns a result that should automatically
  be passed to an additional wrapper, that can be specified here. For example,
  `numpy.zeros` returns a regular `numpy.ndarray` (internally it initializes it
  in the C-extension modules). We need that to be changed to our sub-classed
  `ndarray` so we add `numpy.core.multiarray.zeros=numpy.ndarray` as an option
  to make sure that the result of :func:`numpy.zeros` is always passed through
  the constructor of our `ndarray` subclass.
- **[logging]**: it is possible for an object to be tracked, but *not*
  logged. This makes streamlining work for some methods so that common
  operations can be accelerated without producing log entries. Options are FQDNs
  with a `0` or `1` specifying whether it should be logged or not.
- **[logging.depth]**: specifies the FQDN of certain objects that should be
  logged at a different stack depth than the defaults configured by `acorn`.
- **[streamline]**: options are FQDN with either `0` or `1` as the value. When
  an object is streamlined, acorn logging functionality is disabled for *all*
  sub-calls that are invoked by the top-level call. This makes it almost as fast
  as if `acorn` was never there. However, we still have one extra call for every
  decorated method, so there is a slight performance hit. Streamlining is most
  useful for plotting routines that typically need thousands of method calls,
  many to public, `acorn`\-decorated methods.

.. note::

   In order for an object to be streamlined, it *must* be included in the
   `[tracking]` rules, or `acorn` can never intercept it. To prevent log entries
   from being created, but with streamlining enabled, allow the object to be
   tracked, then add it to `[streamline]` *and* `[logging]` (with a value of
   `0`).
  
.. note::

   Even if a FQDN is specified in `[logging]`, it may still not produced log
   entries if the rules in `[tracking]` prevent it from being decorated in the
   first place.
  
For the `[tracking]`, `[timing]` and `[analysis]` sections, the following
options are available:

- **ignore**: a '$'-separated list of :func:`~fnmatch.fnmatch` styled FQDNs that
  should be ignored during the wrapping. E.g., `matplotlib.set_*` will ignore
  any object in `matplotlib` whose FQDN matches that pattern.
- **rignore**: as for *ignore*, but uses a '$'-separated list of regular
  expression patterns to match against the names. These are compiled and then
  used with :func:`re.match`.
- **filter**: as for *ignore* (also uses :func:`~fnmatch.fnmatch` syntax), but
  specifies FQDNs that should be *included*. Inclusions are handled *before*
  exclusions and thus take a higher priority.
- **filter**: as for *rignore* (also uses regular expression syntax), but
  specifies FQDNs that should be *included*. Inclusions are handled *before*
  exclusions and thus take a higher priority.
   
Global ACORN Configuration
--------------------------

The `acorn.cfg` file has three section options `[acorn.timing]`,
`[acorn.analysis]` and `[acorn.tracking]` that are *globally* configured for all
packages. When a normal package's configuration file is imported, its rules are
augmented with those of the global `acorn` configuration. See the documentation
above for those sections.

Additionally, `acorn` has `[database]` and `[acorn.packages]` sections.

`[database]` Section
^^^^^^^^^^^^^^^^^^^^

Configures the behavior of the database saving methods.

.. todo:: We need to get the database saving to happen using a timer in a
	  separate thread so that the main thread can keep going.

- **folder**: path to the directory where the acorn databases (JSON files)
  should be saved. See also :doc:`database`.
- **savefreq**: specifies how long (in minutes) defore the in-memory collections
  are serialized to JSON and saved to disk. Default: `2`. Since the databases
  can get quite large, this prevents lag in the notebook.

`[acorn.packages]` Section
^^^^^^^^^^^^^^^^^^^^^^^^^^

This section has a simple list of package names with either a `1` (meaning that
the package *should* be auto-decorated when imported from `acorn`) or `0`,
meaning that it *should not* be auto-decorated, even if the user tries to import
it from `acorn`. See :doc:`importer`. E.g., `pywt=1` allows a user to execute
`import acorn.pywt as pywt` even though there isn't an explicit package in
`acorn` called `pywt`.

.. note:: By default, packages *cannot* be automatically imported unless the
	  user has added the package name to this list in `acorn.cfg`. We may
	  decide later that it should be the other way around.
  
API Documentation
-----------------

.. automodule:: acorn.config
   :synopsis: Methods for describing variables and objects in the database.
   :members:
