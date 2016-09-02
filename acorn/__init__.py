# Nothing for now.
from acorn.logging.database import set_task, set_writeable

#Add an exit handler so that in-memory collections are cleaned up correctly and
#saved to disk if the kernel is told to shut down.
import atexit
from acorn.logging.database import cleanup
atexit.register(cleanup)
