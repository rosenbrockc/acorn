# Nothing for now.
from acorn.logging.database import set_task, set_writeable

#Add an exit handler so that in-memory collections are cleaned up correctly and
#saved to disk if the kernel is told to shut down.
import atexit
from acorn.logging.database import cleanup
atexit.register(cleanup)

import acorn.subclass
import acorn.importer

def is_ipython(): # pragma: no cover
    """Returns True if acorn is imported from an ipython notebook or terminal.
    """
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

if is_ipython(): # pragma: no cover
    from IPython import get_ipython
    ipython = get_ipython()
    #Load the ipython extension for automatic decoration of new methods and
    #classes.
    ipython.magic("load_ext acorn.ipython")

import acorn.analyze
