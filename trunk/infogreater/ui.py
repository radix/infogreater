from __future__ import division

from twisted.python import util, components
from twisted.spread.ui import gtk2util

from twisted.internet import defer, reactor

from infogreater import node

import gtk
from gtk import glade, keysyms



import cPickle, os

DEFAULT_FILE = os.path.expanduser('~/.infogreater.data')

GLADE_FILE = util.sibpath(__file__, "info.glade")


__metaclass__ = type


class XML(glade.XML):
    __getitem__ = glade.XML.get_widget

# TODO:
#   *Keyboard navigation
#    *more ideas
#   *Simple nodes to make the common case of FreeMind-like usage acceptable.
#    *Look up INodeUI implementors as adapters of Nodes [Done, but iface needs bettered]
#   *adapting each interface in a node to an IGUI thing?
#   *"caching" of nodes and properties is either too lazy or too
#     strict. fix! facilitate totally dynamic stuff!
#    *What??? I don't know what this point is talking about.
#   *Obsolete manual editing of this TODO list

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
        self.w['NodeFrame'].destroy()

        self.window.connect('destroy', gtk.mainquit)
        self.canvas.connect('expose-event', lambda *a: self.drawLines())
        self.lineGC = gtk.gdk.GC(self.canvas.window)
        self.lineGC.set_rgb_fg_color(BLACK)
        #self.lineGC.line_width = 2
        self.filename = DEFAULT_FILE

        if os.path.exists(DEFAULT_FILE):
            self.basenode = cPickle.load(open(DEFAULT_FILE, 'rb'))
        else:
            self.basenode = node.SimpleNode()
        self.root = INodeUI.fromNode(self.basenode, self, self.canvas)
        self.redisplay()
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
                int(parent.Y+(pheight/2)), box.X, int(box.Y+(bheight/2))
                )
            self.drawLines(box)
        
    def redisplay(self):
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
        self._load(node.SimpleNode())


    def _load(self, node):
        for x in self.canvas.get_children():
            x.destroy()
        self.basenode = node
        self.root = INodeUI.fromNode(self.basenode, self, self.canvas)
        self.redisplay()


    def on_open_activate(self, thing):

        def _cb_got_filename(button):
            fn = select.get_filename()
            select.destroy()
            self.filename = fn
            self._load(cPickle.load(open(fn, 'rb')))

        def _eb_no_filename(button):
            select.destroy()

        select = gtk.FileSelection()
        select.ok_button.connect('clicked', _cb_got_filename)
        select.cancel_button.connect('clicked', _eb_no_filename)
        select.show()

    def _save(self, filename):
        self.filename = filename
        print "dumping", self.basenode, self.basenode.getChildren()
        cPickle.dump(self.basenode, open(self.filename, 'wb'))


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
    def fromNode(node, controller, canvas, parent=None):
        nui = INodeUI(node)
        nui.controller = controller
        nui.canvas = canvas
        nui.parent = parent
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


class BaseNodeUI:
    """
    Make sure subclasses define:
    attr widget: The outermost widget.
    meth _makeWidget: etc
    """
    
    __implements__ = (INodeUI,)

    visible = True
    expanded = True


    V_PAD = 0
    H_PAD = 20

    widget = None

    def __init__(self, node):
        self.node = node
        self.childBoxes = []

    def _internalMakeWidget(self):
        for child in self.node.getChildren():
            self.childBoxes.append(
                INodeUI.fromNode(child, self.controller, self.canvas, parent=self)
                )
        self._makeWidget()


    def calculateHeight(self):
        if not self.widget:
            self._internalMakeWidget()

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
        if not self.widget:
            self._internalMakeWidget()
        # XXX This is *full* of random tweaks! Heh! (and it needs more)
        assert Y >= 0, (X, Y)

        self.widget.hide()
        self.canvas.move(self.widget, X, Y)
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

        # WHAT???? This centers it, but I don't know why it's
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
            # allow it to be. XXX.
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

class SimpleNodeUI(BaseNodeUI):
    editing = False

    # XXX - Conversion to TextViews for SimpleNodes
    # XXX - Conversion to other Node types
    # XXX - cut'n'paste
    # XXX - separate view for cut-buffer?

    def _makeWidget(self):
        self.widget = gtk.Entry()
        self.widget.modify_bg(gtk.STATE_NORMAL, BLACK)
        self.widget.set_text(self.node.getContent())
        self.resize()
        self.widget.set_editable(False)
        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('changed', self._cbChanged)
        self.widget.connect('focus-in-event', self._cbFocus)
        self.widget.connect('focus-out-event', self._cbLostFocus)
        self.canvas.put(self.widget, 0,0)
        self.widget.hide()


    def resize(self):
        # XXX this *1.4 is sucky and buggy. I shouldn't need to mult at _all_!
        self.widget.set_width_chars(
            int(len(self.widget.get_text())*1.4)
            )

    def _cbFocus(self, thing, direction):
        print direction
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)

    def _cbChanged(self, *a):
        self.resize()

    def _cbLostFocus(self, thing, thing2):
        self.widget.modify_base(gtk.STATE_NORMAL, WHITE)
        if self.editing:
            self.cancelEdit()

    def commit(self):
        self.node.setContent(self.widget.get_text())
        self.immute()

    def immute(self):
        self.widget.set_editable(False)
        self.widget.modify_bg(gtk.STATE_NORMAL, BLACK)
        self.widget.modify_base(gtk.STATE_NORMAL, LBLUE)
        self.editing = False
        self.controller.redisplay()
        self.widget.grab_focus()

    def _cbGotKey(self, thing, event):
        print event.keyval
        if event.keyval == keysyms.Insert:
            self.widget.stop_emission('key-press-event')
            self.addChild()
        elif not self.editing:
            self.widget.stop_emission('key-press-event')
            if event.keyval == keysyms.e:
                self.edit()
            elif event.keyval == keysyms.space:
                self.toggleShowChildren()
                self.widget.grab_focus()
            elif event.keyval == keysyms.Right:
                self.moveRight()
            elif event.keyval == keysyms.Left:
                self.moveLeft()
            elif event.keyval == keysyms.Return:
                self.parent.addChild(after=self) #XXX ifacebraking
        elif self.editing:
            if event.keyval == keysyms.Escape:
                self.cancelEdit()
            elif event.keyval == keysyms.Return:
                self.commit()


    def moveRight(self):
        if not self.childBoxes:
            # Hack: don't unfocus the current widget if it's a leafnode.
            # lame: I really ought to be stopping whatever's
            # handling key-press-event from handling it and choosing a
            # widget to focus (it ain't the canvas; i can't figure out
            # _what_ it is)

            # Note: I'm actually relying on the semantics of whatever
            # *is* handling key-press-event here, by letting it choose
            # the widget to focus. Its algorithm is fairly good.
            
            reactor.callLater(0,self.widget.grab_focus)
        elif not self.expanded:
            self.toggleShowChildren()
            reactor.callLater(0, self.childBoxes[0].widget.grab_focus)


    def moveLeft(self):
        if self.parent:
            reactor.callLater(0, self.parent.widget.grab_focus)
        else:
            # lame hack: see moveRight
            reactor.callLater(0,self.widget.grab_focus)


    def edit(self):
        self.oldText = self.widget.get_text()
        self.widget.set_editable(True)
        self.widget.modify_base(gtk.STATE_NORMAL, WHITE)
        self.widget.modify_bg(gtk.STATE_NORMAL, DGREEN)
        #reactor.callLater(0, self.widget.grab_focus)
        self.editing = True


    def cancelEdit(self):
        print "cancelling edit!"
        self.immute()
        self.widget.set_text(self.oldText)
        self.resize()
        del self.oldText
        #reactor.callLater(0, self.widget.grab_focus)


    def addChild(self, after=None):
        newnode = node.SimpleNode()
        newbox = INodeUI.fromNode(newnode, self.controller, self.canvas, parent=self)
        if after is not None:
            index = self.node.children.index(after.node)+1
            self.node.children.insert(index, newnode)
            self.childBoxes.insert(index, newbox)
        else:
            self.node.putChild(newnode)
            self.childBoxes.append(newbox)
            index = -1
        self.controller.redisplay()
        self.childBoxes[index].widget.grab_focus()



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
##        self.canvas.put(self.widget, 0, 0)
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
##        newbox = INodeUI.fromNode(newnode, self.controller, self.canvas, parent=self)
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
