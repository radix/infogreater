from __future__ import division

from twisted.python import util, components
from twisted.spread.ui import gtk2util

from nevow import formless
from infogreater import gtk2form
from twisted.internet import defer

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
#     *Highlight current node
#     *rightarrow : expand children
#     *enter : expand properties
#     *insert : new child

#   *Simple nodes to make the common case of FreeMind-like usage acceptable.
#    *Look up INodeUI implementors as adapters of Nodes
#   *Lines between nodes
#   *formless - mehemeh really crappy support.
#    *Let formless do more... maybe.
#   *"caching" of nodes and properties is either too lazy or too
#     strict. fix! facilitate totally dynamic stuff!
#   *Obsolete manual editing of this TODO list

class GreatUI(gtk2util.GladeKeeper):

    gladefile = GLADE_FILE

    _widgets = ('MainWindow', 'NodeFrame', 'Canvas')


    def __init__(self):
        self.glade = XML(self.gladefile, 'MainWindow')

        ## ripped from gtk2util.py
        # mold can go away when we get a newer pygtk (post 1.99.14)
        mold = {}
        for k in dir(self):
            mold[k] = getattr(self, k)
        self.glade.signal_autoconnect(mold)
        self._setWidgets()
        ## end rip

        # bah, bah, glade is lame.
        self._NodeFrame.destroy()
        #self._SmallNode.destroy()

        self._MainWindow.connect('destroy', gtk.mainquit)

        self.filename = DEFAULT_FILE

        if os.path.exists(DEFAULT_FILE):
            self.basenode = cPickle.load(open(DEFAULT_FILE, 'rb'))
        else:
            self.basenode = node.SimpleNode()
        self.root = INodeUI.fromNode(self.basenode, self, self._Canvas)
        self.redisplay()


    def redisplay(self):
        if not hasattr(self, 'root'):
            from twisted.internet import reactor
            reactor.callLater(0, self.redisplay)
            return
        totalHeight = self.root.getTotalHeight()
        Y = totalHeight // 2
        self.root.redisplay(10, Y)


    def on_new_activate(self, thing):
        self.filename = None
        self._load(node.SimpleNode())


    def _load(self, node):
        for x in self._Canvas.get_children():
            x.destroy()
        self.basenode = node
        self.root = INodeUI.fromNode(self.basenode, self, self._Canvas)
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

    def on_quit_activate(self, thing):
        gtk.mainquit()



class INodeUI(components.Interface):
    """
    XXX ugh, figure out what to do with .height, .expanded, and .childBoxes
    """

    def fromNode(node, controller, canvas):
        nui = INodeUI(node)
        nui.controller = controller
        nui.canvas = canvas
        return nui
    fromNode = staticmethod(fromNode)


    def getTotalHeight(self):
        """
        Return the total height required by this node and all of its
        children...

        XXX: I can't tell what should happen when the node is
        invisible...
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

    V_PAD = 20
    H_PAD = 20

    widget = None

    def __init__(self, node):
        self.node = node

        self.childBoxes = []

    def _internalMakeWidget(self):
        for child in self.node.getChildren():
            self.childBoxes.append(
                INodeUI.fromNode(child, self.controller, self.canvas)
                )
        self._makeWidget()

    def getTotalHeight(self):
        if not self.widget:
            self._internalMakeWidget()

        height = 0
        for x in self.childBoxes:
            height += x.getTotalHeight() + self.V_PAD

        # Sometimes a node's height will be larger than all of its
        # children's.
        myheight = self.widget.size_request()[1]
        height = max(myheight, height)
        
        self.height = height
        return height

    def show(self):
        self.widget.show()

    def hide(self):
        self.widget.hide()
        for child in self.childBoxes:
            child.hide()


class DataNodeUI(BaseNodeUI):

    expanded = False

    def _makeWidget(self):
        self.w = XML(GLADE_FILE, 'NodeFrame')
        self.widget = self.w['NodeFrame']

        if not self.childBoxes:
            self.w['ShowChildrenTog'].hide()

        self.w['NewChildButton'].connect('clicked', self.on_NewChild_clicked)
        self.w['AddButton'].connect('clicked', self.on_AddRow_clicked)
        self.w['ShowChildrenTog'].connect('toggled', self.on_ExpandChildren_toggled)

        self.updateTitle(self.node.getProperty('name', 'Unnamed'))

        #self.w['PropBox'].pack_start(gtk2form.menu(node, self.controller.redisplay))

        # put it at arbitrary location and hide it: let someone reposition it soon.
        self.canvas.put(self.widget, 0, 0)
        self.widget.hide()

        proptog = self.w['ShowPropsTog']
        proptog.set_active(True)
        proptog.connect('toggled', self.on_ExpandButton_toggled)
        proptog.set_active(False)

        self._updateProperties()


    def _updateProperties(self):
        for x in self.w['PropRows'].get_children():
            x.destroy()
        for k,v in self.node.getProperties():
            self.addProp(k,v)


    def redisplay(self, X, Y):
        if not self.widget:
            self._makeWidget()
        # XXX This is *full* of random tweaks! Heh! (and it needs more)
        assert Y >= 0, (X, Y)

        self._updateProperties() # XXX?

        self.widget.hide()
        self.canvas.move(self.widget, X, Y)
        self.widget.show()

        if not (self.expanded and self.childBoxes):
            return

        newX = X + self.widget.size_request()[0] + self.H_PAD
        newY = Y - (self.height // 2)
        first = self.childBoxes[0]
        newY = newY + (first.height // 2)
        first.redisplay(newX, newY)
        prevHeight = first.height

        for child in self.childBoxes[1:]:
            if child.expanded and child.childBoxes:
                newY += (prevHeight // 2) + (child.height // 2)
            else:
                newY += prevHeight
            newY += self.V_PAD
            child.redisplay(newX, newY)
            prevHeight = child.height


    def updateTitle(self, name):
        self.w['Header'].set_text("%s: %s" % (self.node.__class__.__name__, name))


    def on_ExpandChildren_toggled(self, btn):
        self.expanded = not self.expanded
        if self.expanded:
            self.show()
        else:
            self.hide()
        self.controller.redisplay()


    def on_ExpandButton_toggled(self, btn):
        # XXX - if we're a smallnode, convert to framenode.
        if self.visible:
            self.w['PropBox'].hide()
        else:
            self.w['PropBox'].show()
        self.visible = not self.visible
        self.widget.set_size_request(-1, -1)
        self.controller.redisplay()


    def on_NewChild_clicked(self, btn):
        newnode = node.DataNode([])
        self.node.putChild(newnode)
        newbox = INodeUI.fromNode(newnode, self.controller, self.canvas)
        self.childBoxes.append(newbox)

        childtog = self.w['ShowChildrenTog']
        childtog.show()
        childtog.set_active(True)
        self.controller.redisplay()


    def on_AddRow_clicked(self, btn):
        # XXX Add should be made into a configurable that the node supports
        def _cb(*args):
            k = text.get_text()
            self.addProp(k, 'new')
            self.node.setProperty(k, 'new')
            dialog.destroy()
            self.controller.redisplay()
        def _eb(*args):
            dialog.destroy()

        xml = XML(GLADE_FILE, 'AddRowDialog')
        dialog = xml['AddRowDialog']
        text = xml['AddRowEntry']
        text.connect('activate', _cb)
        xml['OkAdd'].connect('clicked', _cb)
        xml['CancelAdd'].connect('clicked', _eb)


    def _cb_save(self, thingy, keye, vale):
        k = keye.get_text()
        v = vale.get_text()
        self.node.setProperty(k, v)
        if k == 'name':
            self.updateTitle(v)


    def _cb_del(self, butt, kl, hb):
        self.node.delProperty(kl.get_text())
        hb.destroy()


    def addProp(self, k, v):
        hb = gtk.HBox()
        kl = gtk.Label()
        kl.set_text(k)
        ve = gtk.Entry()
        ve.set_text(str(v))

        delbutt = gtk.Button('x')
        delbutt.connect('clicked', self._cb_del, kl, hb)

        ve.connect('activate', self._cb_save, kl, ve)

        hb.pack_start(kl, True, True, 0)
        hb.pack_start(ve, False, False, 0)
        hb.pack_start(delbutt, False, False, 0)

        proprows = self.w['PropRows']
        proprows.pack_start(hb, False, False, 0)
        proprows.show_all()

        self.widget.set_size_request(-1, -1)

components.registerAdapter(DataNodeUI, node.DataNode, INodeUI)




class SimpleNodeUI(BaseNodeUI):
    def _makeWidget(self):
        self.widget = gtk.Entry()
        self.widget.set_text(self.node.getContent())
        self.widget.connect('key-press-event', self._cbGotKey)
        self.widget.connect('changed', self._cbCommit)
        # Let someone else display and reposition this widget soon.
        self.canvas.put(self.widget, 0, 0)
        self.widget.hide()

        # XXX - GET RID of expanded. It doesn't make sense for SimpleNodes.
        self.expanded = False

    def _cbCommit(self, thing):
        self.node.setContent(self.widget.get_text())

    def _cbGotKey(self, thing, event):
        if event.keyval == keysyms.Insert:
            self.widget.stop_emission('key-press-event')
            self.addChild()
            

    def addChild(self):
        newnode = node.SimpleNode()
        self.node.putChild(newnode)
        newbox = INodeUI.fromNode(newnode, self.controller, self.canvas)
        self.childBoxes.append(newbox)
        self.controller.redisplay()


    def redisplay(self, X, Y):
        # XXX totally rape'n'pasted from the other redisplay. MUST refactor.
        
        if not self.widget:
            self._makeWidget()
        # XXX This is *full* of random tweaks! Heh! (and it needs more)
        assert Y >= 0, (X, Y)

        self.widget.hide()
        self.canvas.move(self.widget, X, Y)
        self.widget.show()

        if not self.childBoxes:
            return

        newX = X + self.widget.size_request()[0] + self.H_PAD
        newY = Y - (self.height // 2)
        first = self.childBoxes[0]
        newY = newY + (first.height // 2)
        first.redisplay(newX, newY)
        prevHeight = first.height

        for child in self.childBoxes[1:]:
            if child.expanded and child.childBoxes:
                newY += (prevHeight // 2) + (child.height // 2)
            else:
                newY += prevHeight
            newY += self.V_PAD
            child.redisplay(newX, newY)
            prevHeight = child.height


components.registerAdapter(SimpleNodeUI, node.SimpleNode, INodeUI)


