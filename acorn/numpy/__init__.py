# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original numpy package.
import numpy as anp
from acorn.logging.decoration import decorate
decorate(anp)

import sys
sys.modules[__name__] = anp
