# Revision History

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