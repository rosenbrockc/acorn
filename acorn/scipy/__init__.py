# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original scipy package. Scipy is strange
# because it doesn't import any of its subpackages by default. They have to be
# explicitly asked for before they are loaded into the package namespace. So we
# do that here.

#Numpy is almost completely included in scipy; if we want the arrays etc. to be
#handled correctly, we ought to decorate that here as well.
import acorn.numpy

import scipy as asp
from scipy import optimize, spatial, stats, signal, odr, io, constants
from scipy import cluster 
from acorn.logging.decoration import decorate
decorate(asp)

import sys
sys.modules[__name__] = asp
