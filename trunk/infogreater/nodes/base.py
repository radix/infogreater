from __future__ import division

import gtk

from zope import interface

from twisted.internet import defer

from infogreater import facets, xmlobject
from infogreater.gtkgoodies import keyhandler

class INode(interface.Interface):
    """
    Not sure about this. Right now nodes are adapted to this when
    setting parents and children.
    """



class INodeUI(interface.Interface):
    """
    The user interface for interacting with a particular kind of node
    (usually a node.INode implementor, but it doesn't really matter).
    """

    #expanded = property(doc="Whether or not this node's children are visible.")

#    height = property(doc="""The current cached total height of the node.
#XXX(lowpri) This should be unnecessary.""")

    def calculateHeight(self):
        """
        Return the total height required by this node and all of its
        children, and set the 'height' attribute of this node to it.

        I'm pretty sure there are good reasons to explicitly separate
        calculation of the height and access of the cached value. I
        don't think it's reasonably possible to make accessing the
        value transparently recompute it when necessary, because I'm
        not sure when it's necessary. Bleh. Or maybe not, it's
        probably possible after all, but I'm not gonna worry about it
        now!

        I'm pretty sure that when the widget is invisible, it should
        just return 0.
        """


    def redisplay(self):
        """
        Redraw this node and all visible children nodes (preferably by
        calling redisplay() on them!)
        """


    def hide(self):
        """
        Hide this node and all children.
        """


    def focus(self):
        """
        'Select' this node.
        """

STOP_EVENT = True # Just to make it more obvious.

WHITE = gtk.gdk.color_parse('#FFFFFF')
LBLUE = gtk.gdk.color_parse('#AAAAFF')
BLUE = gtk.gdk.color_parse('#0000FF')
GREEN = gtk.gdk.color_parse('#00FF00')
DGREEN = gtk.gdk.color_parse('#00AA00')
BLACK = gtk.gdk.color_parse('#000000')

cuts = []

class BaseNodeUI(facets.Facet, keyhandler.FancyKeyMixin):
    """
    I'm a node that is composed of a single TextView widget.
    I am huge. I will need to be refactored.
    """
    
    interface.implements(INodeUI)

    expanded = True

    V_PAD = 10
    H_PAD = 20

    widget = None

    sized = False

    # XXX I guess this shouldn't be required, but navigation-keys
    # check it. Probably redefine in Simple.. .maybe
    editing = False

    def uiparent(self):
        return INodeUI(INode(self).parent, None)

    def uichildren(self):
        return [INodeUI(x)
                for x in INode(self).getChildren()]


    def _makeWidget(self):
        if self.widget is not None:
            print "I already have a widget :-(((", self
            print "But I'll continue anyway!"
        self.widget = gtk.TextView()
        
        width = INode(self).hasChildren() and 2 or 1
        self.resize_border(width)

        self.widget.modify_bg(gtk.STATE_NORMAL, BLACK)
        self.buffer = self.widget.get_buffer()
        self.buffer.set_text(INode(self).getContent())
        self.widget.set_editable(False)

        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('focus-in-event', self._cbFocus)
        self.widget.connect('focus-out-event', self._cbLostFocus)
        self.widget.connect('size-allocate', self._cbSized)
        self.widget.connect('populate-popup', self._cbPopup)
        #print "PUTTING", self.widget
        self.controller.canvas.put(self.widget, 0, 0)
        self.widget.hide()

    def resize_border(self, width):
        for thingy in (gtk.TEXT_WINDOW_LEFT, gtk.TEXT_WINDOW_RIGHT,
                       gtk.TEXT_WINDOW_TOP, gtk.TEXT_WINDOW_BOTTOM):
            self.widget.set_border_window_size(thingy, width)


    def _cbPopup(self, textview, menu):
        print "HEY POPUP", menu


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
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)
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
        self.widget.modify_base(gtk.STATE_NORMAL, WHITE)
        if self.editing:
            self.cancelEdit()


    def calculateHeight(self):
        height = 0
        if self.expanded:
            for uinode in self.uichildren():
                height += uinode.calculateHeight() + self.V_PAD

        # Sometimes a node's height will be larger than all of its
        # children's.
        myheight = self.widget.size_request()[1]
        height = max(myheight, height)
        
        self.height = height
        return height


    def redisplay(self, X, Y):
        assert Y >= 0, (X, Y)

        self.widget.hide()
        if self.widget.parent is None:
            print "Re-Putting", self
            self.controller.canvas.put(self.widget, 0, 0)
        self.controller.canvas.move(self.widget, X, Y)
        self.X = X
        self.Y = Y

        self.widget.show()


        if not (self.expanded and self.uichildren()):
            return

        # Shift child right by my widget-width plus padding.
        childX = X + self.widget.size_request()[0] + self.H_PAD

        # Shift child up by my *total*-height div 2. (so the parent is
        # in the Y-middle of the children).
        childY = Y - (self.height // 2)

        childBoxes = self.uichildren()
        first = childBoxes[0]

        # WHAT???? XXX This centers it, but I don't know why it's
        # necessary! I would understand it if fixed.moved's arguments
        # were the new *center* of the widget... but that doesn't make
        # sense!
        childY = childY + (first.height // 2)

        first.redisplay(childX, childY)

        prevHeight = first.height

        for child in childBoxes[1:]:

            # Hmm. Why isn't this just "+= prevHeight"?? It screws things
            # up if it is. I think maybe it *should* be prevHeight,
            # but something somewhere *else* is being too annoying to
            # allow it to be. How about that "WHAT???" above? XXX.
            childY += (prevHeight // 2) + (child.height // 2)
            childY += self.V_PAD
            child.redisplay(childX, childY)
            prevHeight = child.height


    def toggleShowChildren(self):
        self.expanded = not self.expanded
        if self.expanded:
            self.showChildren()
        else:
            self.hideChildren()
        self.controller.redisplay()


    def show(self):
        self.widget.show()

    def showChildren(self):
        for child in self.uichildren():
            child.show()


    def hideChildren(self): #hideChildrenAndSelf, really
        self.widget.hide()
        for child in self.uichildren():
            child.hideChildren()


    def destroyChildren(self):
        self.widget.destroy()
        self.widget = None
        for x in self.uichildren():
            x.destroyChildren()


    ## KEYS

    def key_ctrl_l(self):
        self.focus()


    # Navigation

    def key_space(self):
        if self.editing: return
        self.toggleShowChildren()
        self.focus()


    def key_shift_Up(self):
        return self._shift(-1)


    def key_shift_Down(self):
        return self._shift(+1)


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


class DynamicCachingNodeUI(BaseNodeUI):
    """
    Set me on a faceted with an INode that you don't want to traverse
    all at once, and you don't want to keep all children in
    memory.
    """
    # Maybe make this a mixin?
    expanded = False
    def __init__(self, *a, **kw):
        self._cacheChildren = []
        BaseNodeUI.__init__(self, *a, **kw)


    def placedUnder(self, parent):
        INode(self).parent = INode(parent)
        self._makeWidget()


    def uichildren(self):
        return self._cacheChildren


    def showChildren(self):
        children = INode(self).getChildren()
        self._cacheChildren = [INodeUI(x) for x in children]
        BaseNodeUI.showChildren(self)


    def hideChildren(self):
        BaseNodeUI.hideChildren(self)
        for x in self._cacheChildren:
            x.destroyChildren()
        self._cacheChildren = []




class BaseNodeXML(facets.Facet, xmlobject.XMLObject):
    # Relying on order of bases here to say that __init__ comes from
    # Facet and ignore XMLObject's __init__
    tagName = None # set this in subclasses

    def getXMLState(self):
        return self.getAttrs(), self.getChildren()

    def getChildren(self):
        return [xmlobject.IXMLObject(x) for x in INode(self).children]


def presentChoiceMenu(question, choices):
    d = defer.Deferred()

    w = gtk.Window()
    w.connect('destroy',
              lambda *a: (not d.called) and d.errback(Exception("Closed")))
    w.set_title(question)

    vb = gtk.VBox()
    w.add(vb)

    vb.pack_start(gtk.Label(question))
    vbb = gtk.VButtonBox()

    vb.pack_start(vbb)
    for i,choice in enumerate(choices):
        b = gtk.Button(choice)
        print "button", b, choice
        b.connect('clicked', lambda foo, i=i: (d.callback(i), w.destroy()))
        vbb.add(b)

    w.show_all()

    return d

