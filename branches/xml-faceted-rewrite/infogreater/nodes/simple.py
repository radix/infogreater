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

    def getContent(self):
        return self.content
    def setContent(self, content):
        self.content = content

    def getChildren(self):
        return self.children
    def setChildren(self, children):
        self.children = children

    def __str__(self):
        return "<%s content=%r children=%r>" % (self.__class__.__name__, self.content, self.children)
    __repr__ = __str__


class SimpleNodeXML(facets.Facet, xmlobject.XMLObject):
    # Relying on order of bases here to say that __init__ comes from
    # Facet and ignore XMLObject's __init__
    tagName = 'SimpleNode'

    def getXMLState(self):
        return self.getAttrs(), self.getChildren()

    def getAttrs(self):
        nodeui = INodeUI(self)
        return {'visible': str(nodeui.visible),
                'expanded': str(nodeui.expanded)}

    def getChildren(self):
        return [xmlobject.IXMLObject(x) for x in INode(self).children]


    def setXMLState(self, attrs, children):
        node = INode(self)
        node.parent = INode(
            getattr(ctx.get(xmlobject.IXMLParent), 'original', None),
            None)
        node.content = attrs['content']
        node.children = [INode(x) for x in children or []]

        nodeui = INodeUI(self)
        nodeui.visible = xmlobject.boolFromString(attrs['visible'])
        nodeui.expanded = xmlobject.boolFromString(attrs['expanded'])
        nodeui.controller = ctx.get('controller')
        nodeui._makeWidget()

def makeSimpleBase():
    faced = facets.Faceted()
    faced[INode] = SimpleNode(faced)
    faced[INodeUI] = SimpleNodeUI(faced)
    faced[xmlobject.IXMLObject] = SimpleNodeXML(faced)
    return faced

# XXX Use plugins or context something
xmlobject.unmarmaladerRegistry['SimpleNode'] = makeSimpleBase


def makeSimple(controller, parent):
    simp = makeSimpleBase()
    nodeui = INodeUI(simp)
    nodeui.controller = controller
    nodeui._makeWidget()
    node = INode(simp)
    node.parent = INode(parent)
    return simp

STOP_EVENT = True # Just to make it more obvious.

class SimpleNodeUI(base.BaseNodeUI, base.FancyKeyMixin):
    editing = False

    def _makeWidget(self):
        self.widget = gtk.TextView()
        
        width = INode(self).getChildren() and 2 or 1
        self.resize_border(width)

        self.widget.modify_bg(gtk.STATE_NORMAL, base.BLACK)
        self.buffer = self.widget.get_buffer()
        self.buffer.set_text(INode(self).getContent())

        # bleh :( must delay treeing because this is called from
        # __setstate__ before my parent's __setstate__ has been called

        reactor.callLater(0, self.getTreeIter)

        self.widget.set_editable(False)
        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('focus-in-event', self._cbFocus)
        self.widget.connect('focus-out-event', self._cbLostFocus)
        self.widget.connect('size-allocate', self._cbSized)
        self.widget.connect('populate-popup', self._cbPopup)
        print "PUTTING", self.widget
        self.controller.canvas.put(self.widget, 0,0)
        self.widget.hide()


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

    focused = False


    def focus(self):
        if self.widget.is_focus():
            #print "I am the focus! So I will bypass etc."
            return self._cbFocus(None, None)
        self.widget.grab_focus()


    def _cbSized(self, thing, alloc):
        # When a new Node is created it'll get the focus event while
        # the size and position are still -1, -1. So we implement this
        # to scroll to the widget when that happens.

        # Also we need to refocus when the size changes from editing etc.
        if (self.widget.is_focus() and not self.focused) or self.editing:
            #print "_cbSized to tha fizocus"
            self._cbFocus(None,None)

    def _cbFocus(self, thing, direction):
        #print "hey someone got focus man", id(self)
        # set the node to blue
        if thing is not None:
            # UGGh. We're using thing=None here as a heuristic that
            # this is a manually-called _cbFocus instead of the actual
            # event. XXX

            # The point is that this call triggers a size-event, so
            # _cbSized gets called, which calls this. UGH.
            self.widget.modify_base(gtk.STATE_NORMAL, base.LBLUE)

        # scroll the canvas to show the node

        alloc = self.widget.get_allocation()
        # XXX make this optional (it makes current selection always centered)
##        yadj = self.controller.cscroll.get_vadjustment()
##        xadj = self.controller.cscroll.get_hadjustment()

        width, height = self.controller.cscroll.window.get_geometry()[2:4]
##        print width, height
##        yadj.set_value(alloc.y - height/2)
##        xadj.set_value(alloc.x - width/2)
##        return

        # XXX make this optional
        #print "y! x!", alloc.y, alloc.x
        if alloc.y == -1 or alloc.x == -1:
            self.focused = False
            return
        self.focused = True
        for pos, size, windowsize, adj in [
            (alloc.y, alloc.height, height,
             self.controller.cscroll.get_vadjustment()),
            (alloc.x, alloc.width, width,
             self.controller.cscroll.get_hadjustment())
            ]:

            if pos < adj.value or pos+size > adj.value + adj.page_size:
                adj.set_value(pos+(size/2) - windowsize/2)
                #adj.set_value(min(pos, adj.upper - adj.page_size))


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


    def addChild(self, newnode=None, after=None):
        self.resize_border(2)
        if newnode is None:
            newnode = makeSimple(self.controller, self)
        newnode = INode(newnode)
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
        d = presentChoiceMenu("Which node type do you want to create?",
                              [x.__name__ for x in nodeTypes])
        d.addCallback(self._cbGotNodeChoice)

    def _cbGotNodeChoice(self, index):
        nt = nodeTypes[index]
        self.addChild(nt())


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
        children = INode(self).children
        if children:
            INodeUI(children[len(children)//2]).focus()
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
        if self.uiparent():
            index = INode(self).parent.children.index(INode(self))+1
            if len(INode(self).parent.children) <= index:
                #index = 0
                return
            
            INodeUI(INode(self).parent.children[index]).focus()

    key_ctrl_n = key_Down

    def key_Up(self):
        # XXX - Same XXX as key_Down, except reversed.
        if self.editing: return
        i = INode(self).parent.children.index(INode(self))-1
        if i == -1: return
        if self.uiparent():
            INodeUI(INode(self).parent.children[i]).focus()

    key_ctrl_p = key_Up


