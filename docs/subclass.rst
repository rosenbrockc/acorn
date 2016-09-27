Special Sub-classes in ACORN
============================

Some of the special C-extension objects that are wrapped by python run into
issues with decoration. The poster-child for this is :class:`numpy.ndarray`. In
order to have its instance and special method calls be wrapped, the object needs
to be sub-classed using `numpy` specific method calls and syntax (such as
`__arraywrap__`). For cases such as these, `acorn` allows a developer to create
a special module in :module:`acorn.subclass._package`, for a special
package. Thus, `acorn` has a special :class:`numpy.ndarray` subclass in
:module:`acorn.subclass._numpy`. Subclasses are specified in the `acorn`
:doc:`configuration` file so that they can be automatically incorporated by the
decoration machinery.

`numpy` Special Sub-class
-------------------------

.. automodule:: acorn.subclass._numpy
   :synopsis: numpy.ndarray sub-class implementation for logging.
   :members:
