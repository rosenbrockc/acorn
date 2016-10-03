Automatic Decoration of Packages
================================

Every package is different. Some define new built-in types, others use
C-extension modules to optimize the code being run. In a simple world, all the
packages would just be decoratable using standard approaches. However, this
doesn't always work, which is why large and complicated decoration logic was
required to get `acorn` to work.

The basic flow of the decoration is as follows for a new object:

1. Try to determine the fully-qualified domain name (FQDN) of the object, e.g.,
   `numpy.core.multiarray.array`. If the FQDN can be found, proceed to the next
   step; otherwise, we can't decorate the object. This happens very seldomly
   (perhaps 1/10,000 objects).
2. Try to set an attribute on the object. If that works, proceed to step 4;
   otherwise go to step 3.
3. Create an extension for the object. For classes, this means automatically
   sub-classing the object (to inherit all the same attributes as the
   parent). If the object can't be sub-classed, we treat it specially (see
   below) or set it as not-decoratable. For functions, we define a new function
   locally that calls the old one; we then copy across all the attributes of the
   function. Extended objects keep a reference to the original, unextended
   object in the `__acornext__` special attribute.
4. Proceed to decorate the object. For functions and methods, we wrap the object
   using :class:`acorn.logging.decoration.CallingDecorator` and then *overwrite*
   the attribute in the parent object to point to the new function. The original
   function is copied to the `__acorn__` special attribute. If the methods were
   originally static or class methods, we use `staticmethod` and `classmethod`
   to change their behavior. Attributes from the original functions (such as
   `__doc__`) are also copied across so that the function seems identical to the
   end user. For classes, we overwrite the `__new__` method with
   :func:`acorn.logging.decoration.creationlog` and copy the wrapped `__new__`
   to `__old__` on the object. Sometimes packages have multiple references to
   the same object, but located in different parts of the package as attributes
   with different names. When this is discovered, the already-decorated object
   is used in a simple re-assignment of attributes.
5. If the object is of type `classobj` or `module`, we recursively examine each
   of the methods and attributes of the class to determine if they need to be
   decorated or not. Instance methods remain instance methods; class and static
   methods also retain their identity, but are replaced with decorated analogs.

We use aggressive caching of the objects to try and speed things up. We don't
decorate any object that already has an `__acorn__` attribute. Once a package
has been decorated, we don't decorate it ever again.

API Documentation
-----------------

Most of the logic for the decoration is buried in "private" methods of the
module. However, certain public methods are available. However, we recommend to
not call these unless you know what you are doing. It is better to use the
built-in `acorn` importer.

.. automodule:: acorn.logging.decoration
   :synopsis: Methods for decorating arbitrary packages and objects.
   :members:
