Acorn Automated Package Decoration on Import
============================================

Although the most commonly used (and largest) packages have been manually
set-up and corrected for `acorn`, it would be painful for a user to create a new
sub-package in the `acorn` distribution for every package that ever needs to be
decorated. Considering that any pure python package will decorate without any
problems, it would be nice if any package could just be decorated automatically.

`acorn` includes a special module finder
:class:`~acorn.importer.AcornMetaImportFinder` that intercepts all calls to
`import` and can decorate packages "on the fly". The only necessity is that the
package have its name placed in the `[acorn.packages]` section of the
:doc:`configuration` file. Then the package can just be imported using:

.. code-block:: python

   import acorn.package

where `package` is the name of the package. `acorn` intercepts the imports by
using the :data:`sys.meta_path` hook and inserting the `acorn` module finder in
the first position of the list.

API Documentation
-----------------

.. automodule:: acorn.importer
   :synopsis: Meta import finder to intercept python import statements.
   :members:
