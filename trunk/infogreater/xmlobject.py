# -*- test-case-name: infogreater.test.test_xmlobject -*-

from twisted.python import reflect, context as ctx
from infogreater import marmalade
reference = marmalade.reference

class XMLObject(marmalade.DOMJellyable, object):
    """
    A XML persistence mechanism that enforces some knowledge of
    persistence.

    No, it doesn't support __slots__. I hate you.

    This is different from the 'XMLObject' project
    (http://xmlobject.base-art.net/) in that it's more simple and
    dynamic, so it's marginally closer to Pickle. However, it retains
    most of the strict requirement of knowledge of how the object is
    to be persisted; you must put objects to be persisted in the
    'children' attribute, and you can put a mapping of attributes in
    the 'attributes' object. That is, you cannot just persist
    arbitrary objects with this, therefore, there is less room to
    screw up.

    NOTE: References to objects elsewhere in your graph are
    DISALLOWED. If you want a 'secondary reference', use an
    xmlobject.reference(theReferent). The 'referent' attribute of
    'reference' instances gives you the referent object.
    """
    
    def __init__(self, attrs=None, children=None):
        """
        'attrs': (optional) A mapping of strings to strings
        'children': (optional) A sequence of jellyToNode-able objects,
                    respectively.
        """
        self.attrs = attrs
        self.children = children
        self.repr = repr

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

        l = []
        reflect.accumulateClassList(self.__class__, 'contextRemembers', l)
        for contextName, attributeName in l:
            setattr(self, attributeName, ctx.get(contextName))

    def toXML(self):
        return marmalade.jellyToXML(self)


from twisted.python import components
class IXMLParent(components.Interface):
    """
    Nothing required of implementors. This is used as a context key to
    find the parent of an XMLObject during setXMLState.
    """


def fromXML(xml):
    return ctx.call({marmalade.IUnmarmalader: unmarmalader},
                    marmalade.unjellyFromXML, xml)

def unmarmalader(unjellier, element):
    # XXX needs secured
    klass = reflect.namedAny(element.tagName)
    inst = marmalade.instance(klass, {})

    children = None
    if element.childNodes:
        children = [None]*len(element.childNodes)
        i = 0
        for childNode in element.childNodes:
            ctx.call({IXMLParent: inst},
                     unjellier.unjellyInto, children, i, childNode)
            i += 1
    inst.setXMLState(element.attributes, children)
    return inst


