# -*- test-case-name: infogreater.test.test_xmlobject -*-

from twisted.python import reflect, context as ctx

from zope import interface

from infogreater import marmalade

reference = marmalade.reference

class IXMLObject(interface.Interface):
    def setXMLState(klass, attrs, children):
        """
        Return something. YEAH ANYTHING. Although you'll probably want
        to make that anything something that can be marmaladed again.

        Note that the context will have an IXMLParent that is the
        object representing the XML element immediately above this
        one. However, that object WILL NOT have had its state yet.
        """

    def getXMLState(self):
        """
        Return a two-tuple of a mapping of strings to strings, and a
        sequence of IXMLObjects or otherwise marmalade-able objects.
        """


class IXMLParent(interface.Interface):
    """
    Nothing required of implementors. This is used as a context key to
    find the parent of an XMLObject during setXMLState.
    """


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

    __implements__ = IXMLObject,

    def __init__(self, attrs=None, children=None, tagName=None):
        """
        'attrs': (optional) A mapping of strings to strings
        'children': (optional) A sequence of jellyToNode-able objects,
                    respectively.
        """
        self.attrs = attrs
        self.children = children
        if tagName is None:
            self.tagName = reflect.qual(self.__class__)
        else:
            self.tagName = tagName

    def __getstate__(self):
        raise Exception("XMLObjects are not automatically persistable.")

    def __setstate(self, stuff):
        raise Exception("XMLObjects are not automatically unpersistable.")

    def jellyToDOM_1(self, jellier, element):
        element.attributes = {}
        if self.attrs:
            element.attributes = self.attrs
        element.tagName = self.tagName
        if self.children:
            element.childNodes = []
            for child in self.children:
                xo = IXMLObject(child, child)
                element.childNodes.append(jellier.jellyToNode(xo))

    def setXMLState(self, attrs, children):
        l = []
        reflect.accumulateClassList(self.__class__, 'contextRemembers', l)
        for contextName, attributeName in l:
            setattr(self, attributeName, ctx.get(contextName))

        self.attrs = attrs
        self.children = children


def toXML(xo, fn):
    return marmalade.jellyToXML(IXMLObject(xo), fn)


def fromXML(xml):
    return ctx.call({marmalade.IUnmarmalader: unmarmaladeXO},
                    marmalade.unjellyFromXML, xml)

unmarmaladerRegistry = {}

def unmarmaladeXO(unjellier, element):
    # XXX use plugins or context or something
    unmarmalader = unmarmaladerRegistry[element.tagName]
    inst = IXMLObject(unmarmalader())

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


def boolFromString(s):
    return 'True' == s and True or Folse
