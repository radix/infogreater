# -*- test-case-name: infogreater.test.test_xmlobject -*-

import cStringIO

from twisted.python import reflect, context as ctx

from zope import interface

from infogreater import marmalade

reference = marmalade.reference

class IXMLObject(interface.Interface):
    def setXMLState(self, attrs, children, parent):
        """
        @param attrs: A dict of strings to strings from the XML
               attributes.

        @param children: A list of the objects that were represented
               by the children of the XML element.

        @param parent: The object that was represented by the XML
               element immediately above this one. Note that the parent
               WILL NOT have had its state set yet.
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

    Subclasses will want to do various things:
        * implement getXMLState, if you don't like using self.attrs and
          self.children (or don't like having your application code deal
          with them)
        * implement setXMLState manually, for the same reason.
        * set the tagName attribute.
    
    """

    interface.implements(IXMLObject)
    tagName = 'XMLObject'

    def __init__(self, attrs=None, children=None, tagName=None):
        if attrs is None: attrs = {}
        if children is None: children = []

        self.attrs = attrs
        self.children = children

        if tagName is not None:
            self.tagName = tagName

    def __getstate__(self):
        raise Exception("XMLObjects are not automatically persistable.")

    def __setstate(self, stuff):
        raise Exception("XMLObjects are not automatically unpersistable.")

    def jellyToDOM_1(self, jellier, element):
        element.attributes = {}
        attrs, children = self.getXMLState()
        if attrs:
            element.attributes = attrs
        element.tagName = self.tagName
        if children:
            element.childNodes = []
            for child in children:
                xo = IXMLObject(child, child)
                element.childNodes.append(jellier.jellyToNode(xo))

    def setXMLState(self, attrs, children, parent):
        l = []
        reflect.accumulateClassList(self.__class__, 'contextRemembers', l)
        for contextName, attributeName in l:
            setattr(self, attributeName, ctx.get(contextName))
        self.attrs = attrs
        self.children = children
        self.parent = parent

    def getXMLState(self):
        """
        Return a two-tuple of a mapping of strings to strings, and a
        sequence of IXMLObjects or otherwise marmalade-able objects.
        """
        return self.attrs, self.children


def toXML(xo, fn):
    return marmalade.jellyToXML(IXMLObject(xo), fn)

def toXMLString(xo):
    io = cStringIO.StringIO()
    marmalade.jellyToXML(IXMLObject(xo), io)
    return io.getvalue()


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
    inst.setXMLState(element.attributes, children, ctx.get(IXMLParent))
    return inst


