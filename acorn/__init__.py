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
    ip = get_ipython()
    #Load the ipython extension for automatic decoration of new methods and
    #classes.
    ip.magic("load_ext acorn.ipython")

    #Add a javascript event handler for the markdown rendering so that we can
    #log it to the acorn database. The actual javascript is contained in
    #`./js/ipython.js`; we just read it in here and register it with ipython.
    from acorn.utility import reporoot
    from os import path
    jspath = path.join(reporoot, "acorn", "js", "ipython.js")
    with open(jspath) as f:
        jscode = f.read()
    ip.run_cell_magic("javascript", "", jscode)

    #Overwrite the JPEG formatters so that plots produced with inline or
    #notebook modes will be auto-saved as images in the database.
    from acorn.ipython import AcornPNGFormatter, AcornJPEGFormatter
    formatters = ip.display_formatter.formatters
    oldpng = formatters["image/png"]
    formatters["image/png"] = AcornPNGFormatter(parent=oldpng)
    oldjpeg = formatters["image/jpeg"]
    formatters["image/jpeg"] = AcornJPEGFormatter(parent=oldjpeg)
    
import acorn.analyze
