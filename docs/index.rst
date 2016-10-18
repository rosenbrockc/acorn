.. acorn documentation master file, created by
   sphinx-quickstart on Fri Sep 23 15:09:05 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Automatic Computational Research Notebook
=========================================

ACORN automates the decoration and logging of computational research in a smart
way that makes it easy to keep "lab notebooks" for computational
scientists. This API focuses on the python backend that handles all the package
decoration functions needed to implement smart logging.

.. note:: the ipython notebook interface provides logging of commands typed into
	  the notebook. In that way, it is possible to keep a log of everything
	  that was done. However, the log is not as useful as `acorn` because
	  it is just text. We treat variables and methods individually and
	  expose ways to analyze and document results automatically.

The backend is made up a few key pieces:

1. Decorator logic that can handle any kind of package, including the
   C-extension modules that optimize numerical operations.
2. Descriptors that use configuration files to decide how best to describe
   variables/objects in the database. 
3. A database module that saves method calls, object instantiations and the
   objects and variables used in those calls.
4. Automated importer so that new packages (including those created by users)
   can be decorated without modifying `acorn`.
5. `Ipython` extension module that allows classes and functions defined in an
   ipython notebook to be automatically decorated and included in the database.
6. Special sub-classing modules for optimized packages that cannot be handled by
   the default decoration machinery (e.g., `numpy.ndarray`).
7. An analysis module that analyzes the results of certain function calls (based
   on the FQDN of the function) to expose additional features that are
   interesting to the user in the context of a notebook. For example, when a ML
   model is fit, the scores can be configured to automatically be extracted
   whenever `*.predict` is called on the model.
   
Each of these building blocks is described below in a separate documentation
file. Each file also includes the API documentation for the code. Additionally,
the syntax for configuring which parts of packages are included is described in
the :doc:`configuration` section.
   
Contents:

.. toctree::
   :maxdepth: 2

   decoration.rst
   descriptors.rst
   database.rst
   importer.rst
   ipython.rst
   subclass.rst
   analysis.rst
   configuration.rst
	      
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

