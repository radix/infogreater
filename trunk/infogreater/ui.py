from __future__ import division

from twisted.python import util as tputil, components, context
from twisted.spread.ui import gtk2util

from twisted.internet import defer, reactor

from infogreater import node, util

import gtk
from gtk import glade, keysyms



import cPickle, os

DEFAULT_FILE = os.path.expanduser('~/.infogreater.data')

GLADE_FILE = tputil.sibpath(__file__, "info.glade")


__metaclass__ = type


class XML(glade.XML):
    __getitem__ = glade.XML.get_widget


# FFF - draw fancy curves between nodes, not straight lines.
# FFF - Anti-alias the lines between nodes :-)
# FFF - Other node types! UI for creating them?
# FFF - separate view for cut-buffer

class GreatUI(gtk2util.GladeKeeper):

    gladefile = GLADE_FILE

    _widgets = ('MainWindow', 'NodeFrame', 'Canvas')


    def __init__(self, filename=None):
        self.w = XML(self.gladefile, 'MainWindow')

        mold = {}
        for k in dir(self):
            mold[k] = getattr(self, k)
        self.w.signal_autoconnect(mold)

        self.window = self.w['MainWindow']
        self.canvas = self.w['Canvas']
        self.cscroll = self.w['CanvasScroll']
        self.w['NodeFrame'].destroy()

        self.window.connect('destroy', gtk.mainquit)
        self.canvas.connect('expose-event', lambda *a: self.drawLines())
        self.lineGC = gtk.gdk.GC(self.canvas.window)
        self.lineGC.set_rgb_fg_color(BLACK)
        #self.lineGC.line_width = 2
        if filename is not None:
            self.filename = filename
        else:
            self.filename = DEFAULT_FILE

        if os.path.exists(self.filename):
            self.loadFromPickle(self.filename)
        else:
            self.loadNode(node.SimpleNode())

        # XXX HUGE HACK

        # The problem here is that TextViews calculate and update
        # their size_request in an idle call, or something; I can't
        # figure out a way to have them calcualet their size
        # immediately after creation, so I don't know how much room to
        # give them while displaying. I doubt it's possible to do
        # that. So I think the only solution is to give in and just
        # make the layout algorithm incremental, and respond to
        # TextView's size-changing event.

        # XXX This is a huge bug it must be fixed!
        reactor.callLater(0.2, lambda: (self.redisplay(), self.root.widget.grab_focus()))
        # End hack

        self.root.widget.grab_focus()


    def drawLines(self, parent=None):
        if parent is None:
            parent = self.root
        if not parent.expanded: return
        for box in parent.childBoxes:
            # XXX encapsulation
            pwidth, pheight = parent.widget.size_request()
            bheight = box.widget.size_request()[1]
            self.canvas.window.draw_line(
                self.lineGC, parent.X+pwidth,
                parent.Y+(pheight//2), box.X, box.Y+(bheight//2)
            )
            self.drawLines(box)
        
    def redisplay(self):
        """
        Redisplay the whole tree. This should really go away; the tree
        algorithm needs to be made incremental and respond to resizing
        of individual nodes.
        """
        print "I AM REDISPLAYING"
        # Get the height of the entire tree, and position and display
        # the root node half-way down the height.
        width, height = self.canvas.window.get_geometry()[2:4]
        self.canvas.window.clear_area_e(0,0, width, height)
        # xxx god this is fucked
        if not hasattr(self, 'root'):
            reactor.callLater(0, self.redisplay)
            return
        totalHeight = self.root.calculateHeight()
        Y = totalHeight // 2
        self.root.redisplay(10, Y)


    def on_new_activate(self, thing):
        self.filename = None
        self.loadNode(node.SimpleNode())


    def loadFromPickle(self, fn):
        for x in self.canvas.get_children():
            x.destroy()
        root = context.call({'controller': self}, cPickle.load, open(fn, 'rb'))
        self.root = root
        self.basenode = root.node
        self.redisplay()


    def loadNode(self, node):
        for x in self.canvas.get_children():
            x.destroy()
        self.basenode = node
        self.root = INodeUI.fromNode(self.basenode, self)
        self.redisplay()


    def on_open_activate(self, thing):

        def _cb_got_filename(button):
            fn = select.get_filename()
            select.destroy()
            self.filename = fn
            self.loadFromPickle(fn)

        def _eb_no_filename(button):
            select.destroy()

        select = gtk.FileSelection()
        select.ok_button.connect('clicked', _cb_got_filename)
        select.cancel_button.connect('clicked', _eb_no_filename)
        select.show()

    def _save(self, filename):
        self.filename = filename
        print "dumping", self.root
        cPickle.dump(self.root, open(self.filename, 'wb'))


    def on_save_activate(self, thing):
        if self.filename is None:
            self.on_save_as_activate(thing)
            return
        self._save(self.filename)


    def on_save_as_activate(self, thing):

        def _cb_got_filename(button):
            fn = select.get_filename()
            select.destroy()
            self._save(fn)


        def _eb_no_filename(button):
            select.destroy()

        select = gtk.FileSelection()
        select.ok_button.connect('clicked', _cb_got_filename)
        select.cancel_button.connect('clicked', _eb_no_filename)
        select.show()

    def on_debug_activate(self, thing):
        import pdb; pdb.set_trace()

    def on_quit_activate(self, thing):
        gtk.mainquit()



class INodeUI(components.Interface):
    """
    The user interface for interacting with a particular kind of node
    (usually a node.INode implementor, but it doesn't really matter).
    """
    # Not interface.
    def fromNode(node, controller, parent=None):
        nui = INodeUI(node)
        nui.init(controller, parent)
        return nui
    fromNode = staticmethod(fromNode)

    # Interface.

    expanded = property(doc="Whether or not this node's children are visible.")

    height = property(doc="""The current cached total height of the node.
    XXX(lowpri) This should be unnecessary.""")

    childBoxes = property(doc="""The children (list of INodeUIs) of this node.
    XXX Being in the interface is *really* unnecessary, it's only used
    externally for its truth value when doing some display
    calculations. It could probably be replaced with
    hasChildren(). Hell... Shouldn't the 'expand' attribute be fully
    sufficient?""")
    

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


class BaseNodeUI(util.Forgetter):
    """
    Make sure subclasses define:
    attr widget: The outermost widget.
    meth _makeWidget: etc
    """
    
    __implements__ = (INodeUI,)


    visible = True
    expanded = True

    V_PAD = 10
    H_PAD = 20

    widget = None

    def __init__(self, node):
        self.node = node
        self.childBoxes = []


    persistenceForgets = ['controller', 'widget']
    contextRemembers = [('controller', 'controller')]

    def init(self, controller, parent):
        self.controller = controller
        self.parent = parent

        for child in self.node.getChildren():
            self.childBoxes.append(
                INodeUI.fromNode(child, self.controller, parent=self)
                )
        self._makeWidget()

    def __setstate__(self, d):
        util.Forgetter.__setstate__(self, d)
        self._makeWidget()


    def calculateHeight(self):
        height = 0
        if self.expanded:
            for x in self.childBoxes:
                height += x.calculateHeight() + self.V_PAD

        # Sometimes a node's height will be larger than all of its
        # children's.
        myheight = self.widget.size_request()[1]
        height = max(myheight, height)
        
        self.height = height
        return height


    def redisplay(self, X, Y):
        assert Y >= 0, (X, Y)

        self.widget.hide()
        self.controller.canvas.move(self.widget, X, Y)
        self.X = X
        self.Y = Y
        self.widget.show()

        if not (self.expanded and self.childBoxes):
            return

        # Shift child right by my widget-width plus padding.
        childX = X + self.widget.size_request()[0] + self.H_PAD

        # Shift child up by my *total*-height div 2. (so the parent is
        # in the Y-middle of the children).
        childY = Y - (self.height // 2)

        first = self.childBoxes[0]

        # WHAT???? XXX This centers it, but I don't know why it's
        # necessary! I would understand it if fixed.moved's arguments
        # were the new *center* of the widget... but that doesn't make
        # sense!
        childY = childY + (first.height // 2)

        first.redisplay(childX, childY)

        prevHeight = first.height

        for child in self.childBoxes[1:]:

            # Hmm. Why isn't this just "+= prevHeight"?? It screws things
            # up if it is. I think maybe it *should* be prevHeight,
            # but something somewhere *else* is being too annoying to
            # allow it to be. How about that "WHAT???" above? XXX.
            childY += (prevHeight // 2) + (child.height // 2)
            childY += self.V_PAD
            child.redisplay(childX, childY)
            prevHeight = child.height


    def toggleShowChildren(self):
        if not self.childBoxes:
            return
        self.expanded = not self.expanded
        if self.expanded:
            self.show()
        else:
            self.hide()
        self.controller.redisplay()


    def show(self):
        self.widget.show()

    def hide(self):
        self.widget.hide()
        for child in self.childBoxes:
            child.hide()


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
        print event.keyval, repr(event.string), event.state, repr(keymap[event.keyval])
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
        m = getattr(self, name, None)
        if m:
            return m()


STOP_EVENT = True # Just to make it more obvious.


class SimpleNodeUI(BaseNodeUI, FancyKeyMixin):
    editing = False

    persistenceForgets = ['buffer']
    
    def _makeWidget(self):
        self.widget = gtk.TextView()

        width = self.childBoxes and 2 or 1
        self.resize_border(width)

        self.widget.modify_bg(gtk.STATE_NORMAL, BLACK)
        self.buffer = self.widget.get_buffer()
        self.buffer.set_text(self.node.getContent())
        self.widget.set_editable(False)
        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('focus-in-event', self._cbFocus)
        self.widget.connect('focus-out-event', self._cbLostFocus)

        self.controller.canvas.put(self.widget, 0,0)
        self.widget.hide()


    def focus(self):
        self.widget.grab_focus()


    def resize_border(self, width):
        for thingy in (gtk.TEXT_WINDOW_LEFT, gtk.TEXT_WINDOW_RIGHT,
                       gtk.TEXT_WINDOW_TOP, gtk.TEXT_WINDOW_BOTTOM):
            self.widget.set_border_window_size(thingy, width)


    def _cbFocus(self, thing, direction):
        print "hey someone got focus man", id(self)
        # set the node to blue
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)

        # scroll the canvas to show the node

        alloc = self.widget.get_allocation()
        # XXX make this optional
##        yadj = self.controller.cscroll.get_vadjustment()
##        xadj = self.controller.cscroll.get_hadjustment()

        width, height = self.controller.cscroll.window.get_geometry()[2:4]
##        print width, height
##        yadj.set_value(alloc.y - height/2)
##        xadj.set_value(alloc.x - width/2)
##        return

        # XXX make this optional
        for pos, size, windowsize, adj in [
            (alloc.y, alloc.height, height, self.controller.cscroll.get_vadjustment()),
            (alloc.x, alloc.width, width, self.controller.cscroll.get_hadjustment())
            ]:
            if pos < adj.value or pos+size > adj.value + adj.page_size:
                adj.set_value(pos+(size/2) - windowsize/2)
                #adj.set_value(min(pos, adj.upper - adj.page_size))



    def _cbLostFocus(self, thing, thing2):
        self.widget.modify_base(gtk.STATE_NORMAL, WHITE)
        if self.editing:
            self.cancelEdit()

    def immute(self):
        self.widget.set_editable(False)
        self.widget.modify_bg(gtk.STATE_NORMAL, BLACK)
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)
        self.editing = False
        self.controller.redisplay()
        self.focus()


    def addChild(self, newnode=None, after=None):
        self.resize_border(2)
        if newnode is None:
            newnode = node.SimpleNode()
        newbox = INodeUI.fromNode(newnode, self.controller, parent=self)
        if after is not None:
            index = self.node.children.index(after.node)+1
            self.node.children.insert(index, newnode)
            self.childBoxes.insert(index, newbox)
        else:
            self.node.putChild(newnode)
            self.childBoxes.append(newbox)
            index = -1
        self.controller.redisplay()
        print "done redisplaying, focusing new baby", id(self.childBoxes[index])
        # XXX some problem here, for some reason the focus isn't working
        self.childBoxes[index].focus()


    ##################
    ## Key Handlers ##
    ##################

    def key_Insert(self):
        self.addChild()
        return STOP_EVENT


    def key_ctrl_e(self):
        """
        Put into edit mode.
        """
        if self.editing: return
        self.oldText = self.buffer.get_text(*self.buffer.get_bounds())
        self.widget.set_editable(True)
        self.widget.modify_base(gtk.STATE_NORMAL, WHITE)
        self.widget.modify_bg(gtk.STATE_NORMAL, DGREEN)
        self.editing = True

    def destroy_widgets(self):
        self.widget.destroy()
        for x in self.childBoxes:
            x.destroy_widgets()


    def key_ctrl_x(self):
        if self.editing: return
        # XXX YOW encapsulation-breaking
        i = self.parent.node.children.index(self.node)
        del self.parent.node.children[i]
        del self.parent.childBoxes[i]
        self.destroy_widgets()
        self.controller.redisplay()
        self.parent.focus()
        cuts.append(self.node)
        # XXX - there will be other places that destroy nodes soon; refactor 
        if not self.parent.childBoxes:
            # XXX - encapsulation :(
            self.parent.resize_border(1)


    def key_ctrl_v(self):
        if self.editing: return
        self.addChild(cuts.pop())


    def key_space(self):
        if self.editing: return
        self.toggleShowChildren()
        self.focus()


    def _shift(self, modder):
        # XXX encapsulation
        i = self.parent.node.children.index(self.node)
        node = self.parent.node.children.pop(i)
        box = self.parent.childBoxes.pop(i)
        self.parent.node.children.insert(i+modder, node)
        self.parent.childBoxes.insert(i+modder, box)
        self.controller.redisplay()
        self.focus()

    def key_shift_Up(self):
        return self._shift(-1)

    def key_shift_Down(self):
        return self._shift(+1)
        

    def key_Return(self):
        if self.editing:
            self.node.setContent(self.buffer.get_text(*self.buffer.get_bounds()))
            self.immute()
        else:
            # iface?
            self.parent.addChild(after=self)

    def key_Escape(self):
        if not self.editing: return
        self.cancelEdit()

    def cancelEdit(self):
        print "cancelling edit!"
        self.immute()
        self.buffer.set_text(self.oldText)
        del self.oldText
        #reactor.callLater(0, self.focus)



    ## Navigation ##

    def key_Right(self):
        if self.editing: return
        if not self.expanded:
            self.toggleShowChildren()
        if self.childBoxes:
            self.childBoxes[len(self.childBoxes)//2].focus()
        return STOP_EVENT

    key_ctrl_f = key_Right


    def key_Left(self):
        if self.editing: return
        if self.parent:
            self.parent.focus()
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
        if self.parent:
            index = self.parent.childBoxes.index(self)+1
            if len(self.parent.childBoxes) <= index:
                #index = 0
                return
            
            self.parent.childBoxes[index].focus()

    key_ctrl_n = key_Down

    def key_Up(self):
        # XXX - Same XXX as key_Down, except reversed.
        if self.editing: return
        i = self.parent.childBoxes.index(self)-1
        if i == -1: return
        if self.parent:
            self.parent.childBoxes[i].focus()

    key_ctrl_p = key_Up


components.registerAdapter(SimpleNodeUI, node.SimpleNode, INodeUI)

