# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original sklearn package.
from sklearn import *
import sklearn as skl
from acorn.logging.decoration import decorate
decorate(skl)

import sys
sys.modules[__name__] = skl
