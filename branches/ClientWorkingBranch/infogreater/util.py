import os, sys
from twisted.python import util as tputil

def findDataFile(filename):
    for path in (os.path.dirname(__file__),
                 os.path.dirname(sys.executable)):
        fn = os.path.join(path, filename)
        if os.path.isfile(fn):
            return fn
    raise OSError("Couldn't find %s!" % (filename,))
