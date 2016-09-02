# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original pandas package.
import pandas as apd
from acorn.logging.decoration import decorate
decorate(apd)

import sys
sys.modules[__name__] = apd
