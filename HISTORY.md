# Revision History

## Revision 0.0.17

- Changed how the table for the day view of projects is created to give
  us more control over it's format.
- Added get_detailed_view_html in serever/ui/static/js/base.js. This
  function will create the nice views of the log interval details for the
  user.
- Fixed a zabuto_calendar so that it correctly takes a color argument
  to color the dates.
- Started implementing templates for user views of notebooks.

## Revision 0.0.16

- Implemented changes in the user interface server. The Project View is almost complete.

## Revision 0.0.15

- Added the new `ipython.js` file to the package data for acorn so that it gets
  distributed correctly.

## Revision 0.0.14

This revision addresses many of the missing features supporting the
ipython/jupyter notebooks that are breaking features. Any notebook-level loops
are now intercepted and wrapped within a cell function so that they don't
generate millions of database entries; thumbnails get saved to the database (as
long as the plots use PNG and JPEG as display types, we'll support vega and svg
later). Also, diffing between cell executions is now implemented as well. 

- Fixed issues #7, #20 and #25

*NOTE*: unit testing is only up to 93%. We are still missing good unit tests for
`matplotlib` and `sklearn` regressors auto-fit and auto-predict interception is
not tested yet. The ipython notebook support module is now quite large and
doesn't have any unit tests yet. Adding these unit tests will require using js
to emulate the notebooks, etc. which I don't have time for now.

## Revision 0.0.13

- Fixed issue #14.
- Added a function to list all projects and tasks in the database directory.

## Revision 0.0.12

- Fixed `pandas.get` and `pandas.__getitem__` issues.
- Fixed the broken decoration problem; it was caused by the `_cstack_call` depth being too high when an exception was handled by `acorn` or unhandled by `acorn`, but handled by a higher level calling method.
- Fixed the `pytest` internal errors; they were being caused by trying to print the arguments in the `xwrapper` exception handler; now we just print the types of the arguments.

## Revision 0.0.11

- Added two extra ignores to `sklearn` to stop segfaulting problem.

## Revision 0.0.10

- Fixed streamlining for the `pandas` data frame plots by updating the config file. Also added streamlining support for constructors.

## Revision 0.0.9

- Forgot to run unit tests before pushing the package. Fixes a simple typo.

## Revision 0.0.8

- Re-added the pre-import decoration on `scipy`. Forgot to add a comment previously explaining why it had to be there in addition to being in the :func:`decoration.decorate` call.

## Revision 0.0.7

- Added special packages with custom decoration machinery to the setup file so that they would be available as packages after a `pip install`.

## Revision 0.0.6

- Added `acrn.py` setup and configuration file. It allows the custom `~/.acorn` directory to be created with copies of all the default configuration files.
- Added streamlining support for package methods that need to disable all acorn functionality for subsequent method calls. This is useful for high-level methods that need to be logged, but which call thousands of low-level methods that should be ignored (even though such methods are public and may need to be logged in other, direct calls).

## Revision 0.0.5

- Debugged all unit tests for both python 2 and python 3.

## Revision 0.0.4

- Debugged unit tests for `numpy`, `scipy`, `pandas` and `sklearn`.
- `matplotlib` is still having backend trouble (not installed as a framework error) for the testing, so I have disabled the tests for now.

## Revision 0.0.3

- Added severly restricted matplotlib decoration and config file.
- Added automatic decoration for new modules being imported without needing a special package directory in `acorn`. For packages with special importing (such as lazy importers), special packages will still need to be contributed.
- Got `numpy`, `scipy`, `pandas`, `sklearn` and `matplotlib` to all play nicely together (though `sklearn` must be imported first.
- All the tests in the experimenting ipython notebook pass now and are logged correctly.
- Unit tests have mostly been written, but I haven't run and debugged them yet, or set up the CI server, etc.
- API Documentation (but without good examples) setup for the whole package.
