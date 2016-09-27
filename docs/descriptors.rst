ACORN Object Descriptor Interface
=================================

In order for the database to be useful after several years, we need to keep some
extra information about variables that get passed around. We obviously can't
keep copies of every variable (especially true for large matrices); however, we
can keep certain statistics, such as shape, type and other standard statistical
measures. The machinery for describing objects is quite generic and includes
support for attributes, instance methods and calls to other functions that can
return information for a given object.

Descriptor methods are contained within JSON files (named `package.json`, where
'package' is the name of the package where the object is defined). These JSON
files describe dictionaries where the FQDN of an object is the key, and the
value is a dictionary with attributes and values that describe *how to describe*
the object. An object's descriptor dictionary can have the following kinds of
fields:

- **attribute**: can be any attribute of the object; it can also be a FQDN for
  an attribute, specified with a '.'-separated list. E.g., `columns.values`.
- **instance**: is a special keyword that specifies an instance method to be
  called on the object. It's format is described below.

Attribute Descriptor Fields
---------------------------

Attributes are added to the descriptor (dictionary) for an object by specifying
the *name* of the attribute as a key and another dictionary as the value. If the
value dictionary is empty, then the attribute's value will be attached to the
description under the *same name* as the original attribute. However, it can
also be transformed using these options:

- *rename*: expose the value under a new name when describing the object.
- *slice*: if the object is a list or array, you can select columns of the array
  using slice syntax. `name:slice` specifies that the result of taking the slice
  should be set on the descriptor under `name`. `slice` can be a ','-separated
  list of indices to take. For example: `0,1,2` translates to `obj[0][1][2]`.
  .. code-block:: json

     {"values": {"slice": ["mean:1", "std:2"]}}

  will take the **second** column of `values` attribute and label it as `mean`
  on the new object. It will take the **third** column of `values` and place it
  under the attribute `std`. If a name is not specified (i.e., no `:` is present
  in the slice), then it is just labelled by its index in the slice list.
- *transform*: apply a function to the value of the attribute. Functions can
  have `numpy`, `math`, `scipy` in their names. For example, to use the
  square-root of the length of an object, we would use:
  .. code-block:: json
		  
     {"length": {"transform": ["numpy.sqrt"]}}

  which would take attribute `length` and apply `numpy.sqrt` to it. If multiple
  transforms are specified in the list, they will be chained, so that the result
  of the previous item in the list is past to the next transformation.

.. note:: only one of *slice* or *rename* can be specified
  
Instance Method Descriptor Fields
---------------------------------

The instance method descriptors work identically to the standard attribute
descriptors except that instead of operating on a specific attribute of the
object instance, they operate directly on the instance itself. The options
above for *rename* and *slice* work exactly the same way. However, the
*transform* option behaves differently.

If the transform has `self.` in its name, then `self` is replaced by the object
instance. These methods can also be chained and mixed with the `numpy`, `math`
and `scipy` calls.

.. code-block:: json

   {"instance": {"transform": ["self.head", "self.describe", "self.get_values",
   "numpy.sqrt"]}}

would be equivalent to `numpy.sqrt(obj.head().describe().get_values())`.

API Documentation for the Descriptor Machinery
----------------------------------------------

.. automodule:: acorn.logging.descriptors
   :synopsis: Methods for describing variables and objects in the database.
   :members:
