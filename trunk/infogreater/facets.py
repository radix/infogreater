# Taken from Twisted/sandbox/glyph/components/facets.py.
from zope import interface
class IReprable(interface.Interface):
    def repr(self):
        "return a string"

class Faceted(dict):

    __slots__ = ()
    __conform__ = dict.get

    def copy(self):
        copy = self.__class__()
        copy.update(self)
        return copy

    def __repr__(self):
        if IReprable in self:
            return IReprable(self).__repr__()
        return 'Faceted('+super(Faceted, self).__repr__()+')'

class Facet(object):
    def __init__(self, original):
        self.original = original

    def __conform__(self, i):
        if isinstance(self.original, Faceted):
            return self.original.__conform__(i)

    def __repr__(self):
        return "<%s facet of %r>" % (self.__class__.__name__, self.original)

if __name__ == '__main__':

    class IFoo(interface.Interface):
        pass
    class Fooer(Facet):
        pass
    class Reprfancy(Facet):
        def repr(self):
            return "HI"

    faced = Faceted()
    faced[IFoo] = Fooer(faced)
    print IFoo(faced)
    faced[IReprable] = Reprfancy(faced)
    print IFoo(faced)
