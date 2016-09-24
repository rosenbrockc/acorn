Method Call Analysis
====================

Although a log that shows the code a user typed is useful, it lacks the ability
to describe the actual outputs that were examined during the
experimentation. `acorn` allows the result of *any* method that is decorated to
be analyzed by whatever code the user specifies (which may include external
packages).

Methods that will be analyzed, and analysis settings are specified in each
package's configuration file (see :doc:`configuration`).

.. automodule:: acorn.logging.analysis
   :synopsis: Methods for describing variables and objects in the database.
   :members:
