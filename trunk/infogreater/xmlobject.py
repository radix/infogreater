# -*- test-case-name: infogreater.test.test_xmlobject -*-

from twisted.python import reflect, context as ctx
from infogreater import marmalade

class XMLObject(marmalade.DOMJellyable):
    """
    A XML persistence mechanism that enforces some knowledge of
    persistence.

    No, it doesn't support __slots__. I hate you.

    Conceptually, this is different from the 'XMLObject' project in
    that it's more simple and dynamic, so it's marginally closer to
    Pickle; however, it retains most of the strict requirement of
    knowledge of how the object is to be persisted; you must put
    objects to be persisted in the 'children' attribute, and you can
    put a mapping of attributes in the 'attributes' object. That is,
    you cannot just persist arbitrary objects with this, therefore,
    there is less room to screw up.
    """
    def __init__(self, attrs=None, children=None):
        """
        'attrs': (optional) A mapping of strings to strings
        'children': (optional) A sequence of jellyToNode-able objects,
                    respectively.
        """
        self.attrs = attrs
        self.children = children

    def __getstate__(self):
        raise Exception("XMLObjects are not automatically persistable.")

    def __setstate(self, stuff):
        raise Exception("XMLObjects are not automatically unpersistable.")

    def jellyToDOM_1(self, jellier, element):
        element.attributes = {}
        if self.attrs:
            element.attributes = self.attrs
        element.tagName = reflect.qual(self.__class__)
        if self.children:
            element.childNodes = [jellier.jellyToNode(x)
                                  for x in self.children]

    def setXMLState(self, attrs, children):
        self.attrs = attrs
        self.children = children

    def toXML(self):
        return marmalade.jellyToXML(self)

    def fromXML(klass, xml):
        return ctx.call({'unmarmalader': unmarmalader},
                        marmalade.unjellyFromXML, xml)
    fromXML = classmethod(fromXML)

def unmarmalader(unjellier, element):
    children = None
    if element.childNodes:
        children = [None]*len(element.childNodes)
        i = 0
        for childNode in element.childNodes:
            unjellier.unjellyInto(children, i, childNode)
            i += 1
    klass = reflect.namedAny(element.tagName)
    inst = marmalade.instance(klass, {})
    inst.setXMLState(element.attributes, children)
    return inst


