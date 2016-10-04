# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original sklearn package.

from acorn.logging.decoration import set_decorating, decorating
#Before we do any imports, we need to set that we are decorating so that
#everything works as if `acorn` wasn't even here.
origdecor = decorating
set_decorating(True)

from sklearn import *
import sklearn as skl
from acorn.logging.decoration import decorate
decorate(skl)

import sys
sys.modules[__name__] = skl

import acorn.numpy as anp

#Set the decoration back to what it was.
from acorn.logging.decoration import set_decorating
set_decorating(origdecor)
