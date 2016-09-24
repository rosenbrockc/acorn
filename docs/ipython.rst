Ipython Extension Module
========================

Although `acorn` works great with compiled and externally authored modules, part
of the beauty of the ipython experimentation process is that you can create
functions and classes in the notebook for rapid prototyping. In order for
`acorn` to be useful, there needs to be a way for these to be automatically
decorated.

To solve this problem, `acorn` has a special ipython extension module that
registers a callback for the `post_run_cell` event. After a cell is executed,
`acorn` examines all the decoratable objects in the ipython user namespace and
decorates any that haven't already been decorated before. These objects show up
with FQDNs like `__main__.localfunction` in the database log.

API Documentation
-----------------

.. automodule:: acorn.ipython
   :synopsis: Methods for describing variables and objects in the database.
   :members:
