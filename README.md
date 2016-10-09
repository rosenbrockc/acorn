[![Build Status](https://travis-ci.org/rosenbrockc/acorn.svg?branch=master)](https://travis-ci.org/rosenbrockc/acorn)
[![Coverage Status](https://coveralls.io/repos/github/rosenbrockc/acorn/badge.svg?branch=master)](https://coveralls.io/github/rosenbrockc/acorn?branch=master)
[![PyPI](https://img.shields.io/pypi/v/acorn.svg)](https://pypi.python.org/pypi/acorn/)

# Automatic Computational Research Notebook

`acorn` uses the mutability of python objects, together with decorators, to
produce an automatic notebook for computational research. Common libraries like
`numpy`, `scipy`, `sklearn` and `pandas` are mutated with decorators that enable
logging of calls to important methods within those libraries.

This is really helpful for data science where experimenting with fits, pipelines
and pre-processing transformations can result in hundreds of fits and
predictions a day. At the end of the day, it is hard to remember which set of
parameters produced that one fit, which (of course) you didn't realize was
important at the time.

The library is [well documented](https://rosenbrockc.github.io/acorn/).

## Basic Flow

1. Depending on the logging level, every time a method/function is called
(whether bound or unbound), we log it into a JSON database.
2. The JSON database is analyzed using javascript by the browser to produce nice
sets of objects, separated by project, task, date and specific object instances.
3. A nice UI using `bootstrap` populates the HTML dynamically.

## Synchronization

We recommend that the JSON database directory be configured on a Dropbox folder
(later we will support Google Drive, etc.). The HTML notebook can be authorized
(per session) to have access to Dropbox so that the JSON databases can be
accessed from anywhere (and any device). Thi HTML and javascript is completely
standalone (i.e., no server backend required outside of the web service
requests).

## Contribution

If this sparks your interest, please message us. The project is still in early
development, so we can't say more up front.

# Special Notes

The `matplotlib` module is used frequently, but not in the typical way. Most of the methods and objects are used internally unless a plot is being tweaked for some special reason. The `matplotlib.cfg` file prunes the number of objects that get decorate very aggressively so that only the common calls are logged. You can adjust your own local config file if you spend a lot of time actually coding `matplotlib` internals.