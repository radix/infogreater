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


# XXX - When adding new siblings, auto-scrolling is broken.
# XXX - Make layout algo incremental :-(
# XXX - layout breaks on paste of node-with-children.
# XXX - Save layout in files. Pickle node-UIs, I guess...

# FFF - draw fancy curves between nodes, not straight lines.
# FFF - Anti-alias the lines between nodes :-)
# FFF - adapt each interface in a node to an IGUI thing
# FFF - Other node types! UI for creating them?
# FFF - separate view for cut-buffer

class GreatUI(gtk2util.GladeKeeper):

    gladefile = GLADE_FILE

    _widgets = ('MainWindow', 'NodeFrame', 'Canvas')


    def __init__(self):
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
        self.filename = DEFAULT_FILE

        if os.path.exists(DEFAULT_FILE):
            self.loadFromPickle(DEFAULT_FILE)
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
        
        reactor.callLater(0.1, lambda: (self.redisplay(), self.root.widget.grab_focus()))
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
        print "I AM REDISPLAYING"
        width, height = self.canvas.window.get_geometry()[2:4]
        self.canvas.window.clear_area_e(0,0, width, height)
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
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)
        adj = self.controller.cscroll.get_vadjustment()
        alloc = self.widget.get_allocation()        
        if alloc.y < adj.value or alloc.y > adj.value + adj.page_size:
            adj.set_value(min(alloc.y, adj.upper-adj.page_size))


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
        # XXX - crap, cutting nodes-with-children is broken
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


    def key_Right(self):
        if self.editing: return
        if not self.expanded:
            self.toggleShowChildren()
        if self.childBoxes:
            self.childBoxes[len(self.childBoxes)//2].focus()
        return STOP_EVENT


    def key_Left(self):
        if self.editing: return
        if self.parent:
            self.parent.focus()
        return STOP_EVENT

    def key_Down(self):
        if self.editing: return
        if self.parent:
            index = self.parent.childBoxes.index(self)+1
            if len(self.parent.childBoxes) <= index:
                index = 0
            self.parent.childBoxes[index].focus()

    def key_Up(self):
        if self.editing: return
        if self.parent:
            self.parent.childBoxes[self.parent.childBoxes.index(self)+-1].focus()


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





components.registerAdapter(SimpleNodeUI, node.SimpleNode, INodeUI)




##class DataNodeUI(BaseNodeUI):

##    expanded = False

##    def _makeWidget(self):
##        self.w = XML(GLADE_FILE, 'NodeFrame')
##        self.widget = self.w['NodeFrame']

##        if not self.childBoxes:
##            self.w['ShowChildrenTog'].hide()

##        self.w['NewChildButton'].connect('clicked', self.on_NewChild_clicked)
##        self.w['AddButton'].connect('clicked', self.on_AddRow_clicked)
##        self.w['ShowChildrenTog'].connect('toggled', self.on_ExpandChildren_toggled)

##        self.updateTitle(self.node.getProperty('name', 'Unnamed'))

##        #self.w['PropBox'].pack_start(gtk2form.menu(node, self.controller.redisplay))

##        # put it at arbitrary location and hide it: let someone reposition it soon.
##        self.controller.canvas.put(self.widget, 0, 0)
##        self.widget.hide()

##        proptog = self.w['ShowPropsTog']
##        proptog.set_active(True)
##        proptog.connect('toggled', self.on_ExpandButton_toggled)
##        proptog.set_active(False)

##        self._updateProperties()


##    def _updateProperties(self):
##        for x in self.w['PropRows'].get_children():
##            x.destroy()
##        for k,v in self.node.getProperties():
##            self.addProp(k,v)


##    def redisplay(self, X, Y):
##        self._updateProperties() # XXX?



##    def updateTitle(self, name):
##        self.w['Header'].set_text("%s: %s" % (self.node.__class__.__name__, name))


##    def on_ExpandChildren_toggled(self, btn):
##        self.expanded = not self.expanded
##        if self.expanded:
##            self.show()
##        else:
##            self.hide()
##        self.controller.redisplay()


##    def on_ExpandButton_toggled(self, btn):
##        # XXX - if we're a smallnode, convert to framenode.
##        if self.visible:
##            self.w['PropBox'].hide()
##        else:
##            self.w['PropBox'].show()
##        self.visible = not self.visible
##        self.widget.set_size_request(-1, -1)
##        self.controller.redisplay()


##    def on_NewChild_clicked(self, btn):
##        newnode = node.DataNode([])
##        self.node.putChild(newnode)
##        newbox = INodeUI.fromNode(newnode, self.controller, parent=self)
##        self.childBoxes.append(newbox)

##        childtog = self.w['ShowChildrenTog']
##        childtog.show()
##        childtog.set_active(True)
##        self.controller.redisplay()


##    def on_AddRow_clicked(self, btn):
##        # XXX Add should be made into a configurable that the node supports
##        def _cb(*args):
##            k = text.get_text()
##            self.addProp(k, 'new')
##            self.node.setProperty(k, 'new')
##            dialog.destroy()
##            self.controller.redisplay()
##        def _eb(*args):
##            dialog.destroy()

##        xml = XML(GLADE_FILE, 'AddRowDialog')
##        dialog = xml['AddRowDialog']
##        text = xml['AddRowEntry']
##        text.connect('activate', _cb)
##        xml['OkAdd'].connect('clicked', _cb)
##        xml['CancelAdd'].connect('clicked', _eb)


##    def _cb_save(self, thingy, keye, vale):
##        k = keye.get_text()
##        v = vale.get_text()
##        self.node.setProperty(k, v)
##        if k == 'name':
##            self.updateTitle(v)


##    def _cb_del(self, butt, kl, hb):
##        self.node.delProperty(kl.get_text())
##        hb.destroy()


##    def addProp(self, k, v):
##        hb = gtk.HBox()
##        kl = gtk.Label()
##        kl.set_text(k)
##        ve = gtk.Entry()
##        ve.set_text(str(v))

##        delbutt = gtk.Button('x')
##        delbutt.connect('clicked', self._cb_del, kl, hb)

##        ve.connect('activate', self._cb_save, kl, ve)

##        hb.pack_start(kl, True, True, 0)
##        hb.pack_start(ve, False, False, 0)
##        hb.pack_start(delbutt, False, False, 0)

##        proprows = self.w['PropRows']
##        proprows.pack_start(hb, False, False, 0)
##        proprows.show_all()

##        self.widget.set_size_request(-1, -1)

##components.registerAdapter(DataNodeUI, node.DataNode, INodeUI)
