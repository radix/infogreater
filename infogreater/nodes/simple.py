import gtk

from zope import interface

from twisted.python import context as ctx

from infogreater import facets, xmlobject
from infogreater.nodes.base import INode, INodeUI
from infogreater.nodes import base

from twisted.internet import reactor


class SimpleNode(facets.Facet):
    interface.implements(INode)

    def __init__(self, original, content="", parent=None):
        self.original = original
        self.content = content
        self.children = []
	if parent:
            self.parents = [parent]
	else:
	    self.parents = []

    def getParent(self):
        return self.parents

    def addParent(self, parent):
        self.parents.append(parent)

    def getContent(self):
        return self.content

    def setContent(self, content):
        self.content = content

    def getChildren(self):
        return self.children

    def setChildren(self, children):
        self.children = children

    def hasChildren(self):
        return bool(self.getChildren())

    def __str__(self):
        return "<%s at %s content=%r children=%r>" % (self.__class__.__name__,
                                                      hex(id(self)),
                                                      self.content,
                                                      self.children)

    __repr__ = __str__

class SimpleNodeXML(base.BaseNodeXML):
    """
    A node that is editable, and can have children placed under it.
    """
    tagName = 'SimpleNode'

    def getAttrs(self):
        nodeui = INodeUI(self)
        return {'content': INode(self).getContent(),
                'expanded': str(nodeui.expanded)}

    def setXMLState(self, attrs, children, parent):
        node = INode(self)
        node.parent = INode(parent, None)
        node.content = attrs['content']
        node.children = [INode(x) for x in children or []]

        nodeui = INodeUI(self)
        nodeui.expanded = attrs['expanded'] == "True"
        nodeui.controller = ctx.get('controller')
        nodeui._makeWidget()

def makeSimpleBase():
    faced = facets.Faceted()
    faced[INode] = SimpleNode(faced)
    faced[INodeUI] = SimpleNodeUI(faced)
    faced[xmlobject.IXMLObject] = SimpleNodeXML(faced)
    #faced[facets.IReprable] = INode(faced)
    return faced

# XXX Use plugins or context something
xmlobject.unmarmaladerRegistry['SimpleNode'] = makeSimpleBase


def makeSimple(controller, parent=None, content=""):
    simp = makeSimpleBase()
    nodeui = INodeUI(simp)
    node = INode(simp)

    node.parent = parent
    node.content = content

    nodeui.controller = controller
    nodeui._makeWidget()

    return simp

STOP_EVENT = True # Just to make it more obvious.

class SimpleNodeUI(base.BaseNodeUI):
    editing = new = False

    def immute(self):
        self.widget.set_editable(False)
        self.widget.modify_bg(gtk.STATE_NORMAL, base.BLACK)
        self.widget.modify_base(gtk.STATE_NORMAL, base.LBLUE)
        self.editing = False
        self.controller.redisplay()
        self.focus()


    def placedUnder(self, parent):
        INode(self).parent = INode(parent)
        self._makeWidget()
        for x in INode(self).children:
            INodeUI(x).placedUnder(self)


    def addChild(self, newnode=None, after=None):
        self.resize_border(2)
        if newnode is None:
            newnode = makeSimple(self.controller)
        newnode = INode(newnode)
        INodeUI(newnode).placedUnder(self)
        children = INode(self).children
        if after is not None:
            index = children.index(INode(after))+1
            children.insert(index, newnode)
        else:
            children.append(newnode)
            index = -1
        if not self.expanded:
            self.toggleShowChildren()
        self.controller.redisplay()
        # XXX some problem here, for some reason the focus isn't working
        self.uichildren()[index].focus()

        return newnode


    ##################
    ## Key Handlers ##
    ##################

    def key_Insert(self):
        """
        Insert a simple child node.
        """
        newnode = self.addChild()
        nodeui = INodeUI(newnode)
        nodeui.startEdit()
        nodeui.new = True
        return STOP_EVENT

    key_ctrl_i = key_Insert


    def key_Return(self):
        """
        Either commit the text that was being edited, or insert a new
        sibling node after this one.
        """
        if self.editing:
            INode(self).setContent(
                self.buffer.get_text(*self.buffer.get_bounds()))
            self.immute()
            self.new = False
        else:
            # iface?
            newnode = self.uiparent().addChild(after=INode(self))
            nodeui = INodeUI(newnode)
            nodeui.startEdit()
            nodeui.new = True


    def key_shift_I(self):
        """
        Insert a _special_ child node.
        """
        if self.editing: return
        d = base.presentChoiceMenu("Which node type do you want to create?",
                                   [x[0] for x in base.nodeTypes])
        d.addCallback(self._cbGotNodeChoice)

    def _cbGotNodeChoice(self, index):
        factory = base.nodeTypes[index][1]
        self.addChild(factory(self.controller))


    def key_ctrl_e(self):
        """
        Put into edit mode.
        """
        if self.editing: return
        self.startEdit()

    def startEdit(self):
        self.oldText = self.buffer.get_text(*self.buffer.get_bounds())
        self.widget.set_editable(True)
        self.widget.modify_base(gtk.STATE_NORMAL, base.WHITE)
        self.widget.modify_bg(gtk.STATE_NORMAL, base.DGREEN)
        self.editing = True


    def key_ctrl_x(self):
        """
        cut
        """
        if self.editing: return
        self.uiparent().destroyChild(self)
        base.cuts.append(self)


    def destroyChild(self, child):
        # XXX this Really needs to be on the model, + model-changed
        # events.
        snode = INode(self)
        i = snode.children.index(INode(child))
        del snode.children[i]
        INodeUI(child).destroyChildren()
        self.controller.redisplay()
        self.focus()

        if not snode.children:
            self.resize_border(1)


    def key_ctrl_v(self):
        """
        paste
        """
        if self.editing: return
        self.addChild(base.cuts.pop())


    def _shift(self, modder):
        # XXX encapsulation
## 	assert(False)
        sibs = INode(self).parent.children
        i = sibs.index(INode(self))
        print "moving from",i,"to",i+modder
        # XXX sucks to this
        box = sibs.pop(i)
        sibs.insert(i+modder, box)
        self.controller.redisplay()
        self.focus()


    def key_Escape(self):
        if not self.editing: return
        self.cancelEdit()


    def cancelEdit(self):
        print "cancelling edit!"
        self.immute()
        self.buffer.set_text(self.oldText)
        del self.oldText
        if self.new:
            self.uiparent().destroyChild(self)
        #reactor.callLater(0, self.focus)
