from __future__ import division

import gtk
from gtk import keysyms

from zope import interface

from infogreater import facets

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


class BaseNodeUI(facets.Facet):
    """
    Make sure subclasses define:
    attr widget: The outermost widget.
    meth _makeWidget: etc
    """
    
    __implements__ = (INodeUI,)

    expanded = True

    V_PAD = 10
    H_PAD = 20

    widget = None

    def init(self, controller):
        self.controller = controller
        self._makeWidget()

    def uiparent(self):
        return INodeUI(INode(self).parent, None)

    def uichildren(self):
        return [INodeUI(x)
                for x in INode(self).getChildren()]


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
            self.controller.canvas.put(self.widget, 0,0)
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
        for x in self.uichildren():
            x.destroyChildren()



WHITE = gtk.gdk.color_parse('#FFFFFF')
LBLUE = gtk.gdk.color_parse('#AAAAFF')
BLUE = gtk.gdk.color_parse('#0000FF')
GREEN = gtk.gdk.color_parse('#00FF00')
DGREEN = gtk.gdk.color_parse('#00AA00')
BLACK = gtk.gdk.color_parse('#000000')

cuts = []

keymap = {}
for name in dir(keysyms):
    try:
        keymap[getattr(keysyms, name)] = name
    except TypeError:
        pass

class FancyKeyMixin:
    def _cbGotKey(self, thing, event):

        mods = []
        if event.state & gtk.gdk.CONTROL_MASK:
            mods.append('ctrl')
        if event.state & gtk.gdk.SHIFT_MASK:
            mods.append('shift')
        mod = '_'.join(mods)
        keyname = keymap[event.keyval]
        if mod:
            name = 'key_%s_%s' % (mod, keyname)
        else:
            name = 'key_%s' % keyname
        print event.keyval, repr(event.string), event.state, repr(keymap[event.keyval]), name
        m = getattr(self, name, None)
        if m:
            return m()


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

