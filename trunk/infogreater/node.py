"""

The model is almost a directed acyclic graph (tree) whose nodes have
properties. The properties are made of string names and arbitrary
values. One type of value that will definitely be supported are other
nodes: thus our DAG has an 'out-of-band' way to become a simple DG :)

The reason for two different ways of linking to other nodes is to
facilitate the UI: Making the 'real' graph a DAG makes it easy to do
layout: laying out a tree of nodes is easy, and offers a canonical
display of the graph. The property-links will probably be displayed as
buttons which will reposition the UI view to the linked-to node.

"""

#from nevow import formless
from twisted.python import components

# Potential features::
#  INode's parent. Could be done with a context object.

#  * Make INode empty or almost empty. Then have IPropertiesNode and IChildrenNode
#    * IPropertiesNode will be a TypedInterface.  UI code will look at
#      IPropertiesNode and render it special. (in the top-level widget,
#      rather than a button to it)
#    * IChildrenNode also a TypedInterface? Meh

#  Node-specific UI extensions::
#   * Reordering of properties
#   * adding a child to an InMemory.

class INode(components.Interface):
    def getChildren(self):
        """
        Return the children of this node as a sequence.
        """

    def putChild(self, node):
        """
        Add a child node to this node.
        """

class INodeProperties(components.Interface):


    def getProperty(self, name, default=None):
        """
        Return the value of property 'name' (in a Deferred, perhaps).

        If the property is not available, and the default is
        specified, return it. Otherwise, raise KeyError if the
        property is not available.
        """


    def setProperty(self, name, value):
        """
        Set the value of property 'name' to 'value'.
        """


    def delProperty(self, name):
        """
        Try to remove this property.
        """


    def getProperties(self):
        """
        Return an iterable of ('name', value) pairs. name must be
        string, value can be anything (In a Deferred, perhaps).
        """


##class INodeChildren(formless.TypedInterface):
##    def getChildren(self):
##        """
##        Return an iterable of INode implementors.
##        """



##class PropertyName(formless.String):
##    def coerceWithBinding(self, val, configurable):
##        val = str(val)
##        for propname,v in configurable.properties:
##            if propname == name:
##                raise formless.InputError("%s is already a property" % val)
##        return val



class BaseNode:
    __implements__ = (INode,)

    ## INode

    def getChildren(self):
        return self.children

    def putChild(self, obj):
        self.children.append(obj)


class DataNode(BaseNode):

    __implements__ = (BaseNode.__implements__, INodeProperties)

    def __init__(self, properties, children=None):
        """
        Instantiate me with a sequence of pairs, and perhaps a set of children.
        """
        if children is None:
            children = []
        self.children = children
        self.properties = list(properties)




##    def clear(self):
##        del self.children[:]
##        del self.properties[:]


    ## INodeProperties

    def getProperty(self, name, default=None):
        for k,v in self.properties:
            if k == name: return v
        if default:
            return default
        raise KeyError("%s not found during get" % name)


    def setProperty(self, name, value):
        for i, pair in enumerate(self.properties):
            if pair[0] == name:
                self.properties[i] = (name, value)
                return
        self.properties.append((name,value))


    def delProperty(self, name):
        for i, pair in enumerate(self.properties):
            if pair[0] == name:
                del self.properties[i]
                return
        raise KeyError("%s not found during delete" % name)


    def getProperties(self):
        return self.properties

class SimpleNode(BaseNode):
    
    def __init__(self, content='', children=None):
        self.content = content
        if children is None:
            children = []
        self.children = children


    def getContent(self):
        return self.content


    def setContent(self, crap):
        self.content = crap

