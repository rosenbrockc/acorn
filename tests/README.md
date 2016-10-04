# Testing Approach

The `acorn` unit tests are focused on commonly-used packages to make sure that
they all decorate and log correctly. This indirectly tests all other parts of
the code-base (described in the [API
Documentation](https://rosenbrockc.github.io/acorn/)). The repo is setup with
continuous integration on [travis](https://travis-ci.org/profile/rosenbrockc)
and [coveralls](https://coveralls.io/github/rosenbrockc/acorn) and uses `tox` to
test the decoration on `python2` and `python3`.

To run the unit tests locally, use:

```
pytest
```

from the repository root; or, to run with coverage checks, use:

```
coverage run --source=acorn -m pytest
```

If a new package causes trouble on decoration, we usually debug it in an
`ipython` notebook. Once we have the problem sorted out (and haven't broken any
existing functionality), we create a test module here called `test_[package].py`
for the package. It should broadly test the most frequent tasks in the package.

## Some Reminders

Most packages include some mixture of all the different kinds of objects. At a
minimum, you should usually look for:

- class initialization
- instance methods
- static and class methods
- regular functions

Other packages with C-extensions or low-level C or Fortran optimization
sometimes declare additional built-in functions or do other strange
things. These should also be tested.

# Notes

`sklearn` uses C-extension modules for some of the algorithms (like
`libsvm`). These are low-level optimized for *standard* `ndarray` instances. We
have to use sub-classed `ndarray` to get `acorn` to work
properly. Unfortunately, these cannot be cast low-level in `sklearn`. However,
we can still get them to play nicely together as long as we import `sklearn`
*first*.

Since `pytest` orders the files by name before executing the tests, we can get
the `sklearn` importing and testing to run first by changing the file name for
that test module to `test_0sklearn.py`, where the `0` causes it to be done
first.