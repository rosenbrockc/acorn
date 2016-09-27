# Revision History

# Revision 0.0.3

- Added severly restricted matplotlib decoration and config file.
- Added automatic decoration for new modules being imported without needing a special package directory in `acorn`. For packages with special importing (such as lazy importers), special packages will still need to be contributed.
- Got `numpy`, `scipy`, `pandas`, `sklearn` and `matplotlib` to all play nicely together (though `sklearn` must be imported first.
- All the tests in the experimenting ipython notebook pass now and are logged correctly.
- Unit tests have mostly been written, but I haven't run and debugged them yet, or set up the CI server, etc.