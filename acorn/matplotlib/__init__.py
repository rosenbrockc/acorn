from acorn.logging.decoration import set_decorating, decorating
#Before we do any imports, we need to set that we are decorating so that
#everything works as if `acorn` wasn't even here.
origdecor = decorating
set_decorating(True)

import matplotlib as mpl
from matplotlib import pyplot, axes, figure

from acorn.logging.decoration import decorate
decorate(mpl)

import sys
sys.modules[__name__] = mpl

#Set the decoration back to what it was.
from acorn.logging.decoration import set_decorating
set_decorating(origdecor)
