# We import the decoration logic from acorn and then overwrite the sys.module
# for this package with the decorated, original sklearn package.

from acorn.logging.decoration import set_decorating, decorating
#Before we do any imports, we need to set that we are decorating so that
#everything works as if `acorn` wasn't even here.
origdecor = decorating
set_decorating(True)

#Sklearn doesn't play well with subclassed ndarray instances... We end up
#tricking python into thinking that numpy isn't loaded yet. It will load
#(quickly) a clean version of numpy (without decorators and subclassed ndarray)
#and then sklearn will be happy to work with those.
from acorn.importer import scratch
removed = {}
#scratch("numpy", removed)

from sklearn import *
import sklearn as skl
from acorn.logging.decoration import decorate
decorate(skl)

import sys
sys.modules[__name__] = skl

#This is rather sad and a little wasteful; but we have to redecorate numpy now
#that it has been reloaded. If the person import sklearn first, then they save
#time; otherwise we just have to do this again...
from acorn.importer import restore
#restore("numpy")
import acorn.numpy as anp

#Set the decoration back to what it was.
from acorn.logging.decoration import set_decorating
set_decorating(origdecor)
