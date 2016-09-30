# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original scipy package. Scipy is strange
# because it doesn't import any of its subpackages by default. They have to be
# explicitly asked for before they are loaded into the package namespace. So we
# do that here.

from acorn.logging.decoration import set_decorating, decorating

#Before we do any imports, we need to set that we are decorating so that
#everything works as if `acorn` wasn't even here.
origdecor = decorating
set_decorating(True)

import scipy as asp
from scipy import optimize, spatial, stats, signal, odr, io, constants
from scipy import cluster 
from acorn.logging.decoration import decorate
decorate(asp)

#Because scipy uses a lot of numpy, we run into problems where top-level scipy
#members point to the *undecorated* numpy objects. Here we just ensure that all
#of scipy is decorated.
from acorn.logging.decoration import postfix
postfix(asp)

import sys
sys.modules[__name__] = asp

#Set the decoration back to what it was.
from acorn.logging.decoration import set_decorating
set_decorating(origdecor)
