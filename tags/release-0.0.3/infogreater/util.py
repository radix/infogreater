#Copyright Divmod! LGPL!
from twisted.python import reflect, context
from twisted.persisted import styles

class Forgetter:
    """Utility class for forgetting particular attributes when persisted.

    @cvar persistenceForgets: A list of strings, naming attributes which should
    be deleted when I am persisted.

    @cvar contextRemembers: A list of 2-tuples of strings, (contextName,
    attributeName), that name attributes which should be retrieved from
    twisted.python.context upon loading me.
    """

    def __getstate__(self, state=None):
        if state is None:
            state = self.__dict__.copy()
        if isinstance(self, styles.Versioned):
            d = styles.Versioned.__getstate__(self, state)
        else:
            d = state
        l = []
        reflect.accumulateClassList(self.__class__, 'persistenceForgets', l)
        for ig in l:
            if d.has_key(ig):
                del d[ig]
        return d

    def __setstate__(self, state):
        if isinstance(self, styles.Versioned):
            styles.Versioned.__setstate__(self, state)
        else:
            self.__dict__ = state
        l = []
        reflect.accumulateClassList(self.__class__, 'contextRemembers', l)
        for contextName, attributeName in l:
            setattr(self, attributeName, context.get(contextName))
