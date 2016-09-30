# Revision History

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