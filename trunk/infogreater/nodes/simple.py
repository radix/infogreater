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
        self.parent = parent

    def _setContent(self, v):
        if v == 'Ha!':
            print "OH CRAP"
            import traceback
            traceback.print_stack()
        self._content = v

    content = property(lambda s: s._content,
                       _setContent)


    def getContent(self):
        return self.content
    def setContent(self, content):
        self.content = content

    def getChildren(self):
        return self.children
    def setChildren(self, children):
        self.children = children

    def __str__(self):
        return "<%s at %s content=%r children=%r>" % (self.__class__.__name__,
                                                      hex(id(self)),
                                                      self.content,
                                                      self.children)
    __repr__ = __str__


class SimpleNodeXML(base.BaseNodeXML):
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

class SimpleNodeUI(base.BaseNodeUI, base.FancyKeyMixin):
    editing = False

    def _makeWidget(self):
        if self.widget is not None:
            print "Booo Hoooooo, I already have a widget :-(((", self
            return
        self.widget = gtk.TextView()
        
        width = self.hasChildren() and 2 or 1 
        self.resize_border(width)

        self.widget.modify_bg(gtk.STATE_NORMAL, base.BLACK)
        self.buffer = self.widget.get_buffer()
        self.buffer.set_text(INode(self).getContent())

        # bleh :( must delay treeing because _makeWidget can be called
        # before my parent has been fully unserialized.
        reactor.callLater(0, self.getTreeIter)

        self.widget.set_editable(False)
        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('focus-in-event', self._cbFocus)
        self.widget.connect('focus-out-event', self._cbLostFocus)
        self.widget.connect('size-allocate', self._cbSized)
        self.widget.connect('populate-popup', self._cbPopup)
        #print "PUTTING", self.widget
        self.controller.canvas.put(self.widget, 0, 0)
        self.widget.hide()

    def hasChildren(self):
        return INode(self).getChildren() and 2 or 1


    def getTreeIter(self):
        if hasattr(self, 'treeiter'):
            return self.treeiter
        if self.uiparent() == None:
            parentiter = None
        else:
            parentiter = self.uiparent().getTreeIter()
        self.treeiter = self.controller.tree.add(
            {'Node': INode(self).getContent()}, parentiter)
        return self.treeiter


    def resize_border(self, width):
        for thingy in (gtk.TEXT_WINDOW_LEFT, gtk.TEXT_WINDOW_RIGHT,
                       gtk.TEXT_WINDOW_TOP, gtk.TEXT_WINDOW_BOTTOM):
            self.widget.set_border_window_size(thingy, width)


    def _cbPopup(self, textview, menu):
        print "HEY POPUP", menu


    sized = False

    def focus(self):
        # XXX I don't remember why this does this.
        if self.widget.is_focus():
            #print "I am the focus! So I will bypass etc."
            return self._recenter()
        self.widget.grab_focus()


    def _cbSized(self, thing, alloc):
        # When a new Node is created it'll get the focus event while
        # the size and position are still -1, -1. So we implement this
        # to scroll to the widget when it gets initially sized.

        # Also we want to recenter when the size changes from the user
        # typing into it.
        if (self.widget.is_focus() and not self.sized) or self.editing:
            #print "_cbSized to tha fizocus"
            self._recenter()

    def _cbFocus(self, thing, direction):
        """
        Set the node to blue and recenter to it.
        """
        # The reason this modify_base is here instead of in _recenter
        # is that this call triggers a size-event: _recenter is called
        # from the size-event handler (_cbSized), so we have to avoid
        # the infinite loop.
        self.widget.modify_base(gtk.STATE_NORMAL, base.LBLUE)
        return self._recenter()

    def _recenter(self):
        """
        Position the canvas so that this node is in the center.
        """

        alloc = self.widget.get_allocation()
        width, height = self.controller.cscroll.window.get_geometry()[2:4]

        # XXX some horrible hackiness to avoid infinite event-recursion.
        if alloc.y == -1 or alloc.x == -1:
            self.sized = False
            return
        self.sized = True

        for pos, size, windowsize, adj in [
            (alloc.y, alloc.height, height,
             self.controller.cscroll.get_vadjustment()),
            (alloc.x, alloc.width, width,
             self.controller.cscroll.get_hadjustment())
            ]:

            if pos < adj.value or pos+size > adj.value + adj.page_size:
                adj.set_value(pos+(size/2) - windowsize/2)


    def _cbLostFocus(self, thing, thing2):
        self.widget.modify_base(gtk.STATE_NORMAL, base.WHITE)
        if self.editing:
            self.cancelEdit()

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
        self.controller.redisplay()
        # XXX some problem here, for some reason the focus isn't working
        self.uichildren()[index].focus()


    ##################
    ## Key Handlers ##
    ##################

    def key_Insert(self):
        self.addChild()
        return STOP_EVENT

    key_ctrl_i = key_Insert

    def key_shift_I(self):
        if self.editing: return
        print "HEY"
        d = base.presentChoiceMenu("Which node type do you want to create?",
                                   [x.__name__ for x in base.nodeTypes])
        d.addCallback(self._cbGotNodeChoice)

    def _cbGotNodeChoice(self, index):
        factory = base.nodeTypes[index]
        self.addChild(factory(self.controller))


    def key_ctrl_e(self):
        """
        Put into edit mode.
        """
        if self.editing: return
        self.oldText = self.buffer.get_text(*self.buffer.get_bounds())
        self.widget.set_editable(True)
        self.widget.modify_base(gtk.STATE_NORMAL, base.WHITE)
        self.widget.modify_bg(gtk.STATE_NORMAL, base.DGREEN)
        self.editing = True

    def key_ctrl_x(self):
        if self.editing: return
        snode = INode(self)
        # XXX YOW encapsulation-breaking
        i = snode.parent.children.index(snode)
        del INode(self).parent.children[i]
        self.destroyChildren()
        self.controller.redisplay()
        self.uiparent().focus()
        base.cuts.append(self)
        # XXX - there will be other places that destroy nodes soon; refactor
        # self.parent.lostChild() or something
        if not INode(self).parent.children:
            self.uiparent().resize_border(1)


    def key_ctrl_v(self):
        if self.editing: return
        self.addChild(base.cuts.pop())


    def key_space(self):
        if self.editing: return
        self.toggleShowChildren()
        self.focus()


    def _shift(self, modder):
        # XXX encapsulation
        i = self.parent.children.index(self)
        # XXX sucks to this
        box = self.parent.children.pop(i)
        self.parent.children.insert(i+modder, box)
        self.controller.redisplay()
        self.focus()


    def key_shift_Up(self):
        return self._shift(-1)

    def key_shift_Down(self):
        return self._shift(+1)
        

    def key_Return(self):
        if self.editing:
            INode(self).setContent(
                self.buffer.get_text(*self.buffer.get_bounds()))
            self.immute()
        else:
            # iface?
            self.uiparent().addChild(after=INode(self))

    def key_Escape(self):
        if not self.editing: return
        self.cancelEdit()

    def cancelEdit(self):
        print "cancelling edit!"
        self.immute()
        self.buffer.set_text(self.oldText)
        del self.oldText
        #reactor.callLater(0, self.focus)

    def key_ctrl_l(self):
        self.focus()



    ## Navigation ##

    def key_Right(self):
        if self.editing: return
        if not self.expanded:
            self.toggleShowChildren()
        children = self.uichildren()
        if children:
            children[len(children)//2].focus()
        return STOP_EVENT

    key_ctrl_f = key_Right


    def key_Left(self):
        if self.editing: return
        parent = INode(self).parent
        if parent:
            print "no parent"
            INodeUI(parent).focus()
        return STOP_EVENT

    key_ctrl_b = key_Left

    def key_Down(self):

        # XXX - if there's nothing below, traverse parents backward
        # (up the tree) until I find one that has a lower sibling;
        # check the lower sibling if it has a node as many levels deep
        # as I traversed up; switch to it. If it doesn't, keep going
        # back/down until I find one.

        # A - B - C <-- hits downarrow when C is selected
        # | 
        # D - E
        # |
        # F - G - H <-- should end up here.
        
        if self.editing: return
        if not self.uiparent(): return
        sibs = self.uiparent().uichildren()
        index = sibs.index(self)+1
        if len(sibs) <= index:
            #index = 0
            return

        sibs[index].focus()

    key_ctrl_n = key_Down

    def key_Up(self):
        # XXX - Same XXX as key_Down, except reversed.
        if self.editing: return
        if not self.uiparent(): return

        sibs = self.uiparent().uichildren()
        i = sibs.index(self)-1
        if i == -1:
            return
        sibs[i].focus()

    key_ctrl_p = key_Up


