from __future__ import division

from cStringIO import StringIO
import os

from zope import interface

from twisted.python import util as tputil, context as ctx
from twisted.spread.ui import gtk2util
from twisted.internet import defer, reactor

import gtk
from gtk import glade
from gtkgoodies import tree

from infogreater import util, facets, xmlobject
from infogreater.nodes import base



DEFAULT_FILE = os.path.expanduser('~/.infogreater.data')
GLADE_FILE = tputil.sibpath(__file__, "info.glade")

__metaclass__ = type

class XML(glade.XML):
    __getitem__ = glade.XML.get_widget

# FFF - draw fancy curves between nodes, not straight lines.
# FFF - Anti-alias the lines between nodes :-)
# FFF - Other node types! UI for creating them?
# FFF - separate view for cut-buffer

BLACK = gtk.gdk.color_parse('#000000')

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

        self.tree = tree.Tree(self.w['NodeTree'], [('Node', str)])

        if filename is not None:
            self.filename = filename
        else:
            self.filename = DEFAULT_FILE

        if os.path.exists(self.filename):
            self.loadFromXML(self.filename)
        else:
            self.loadNode(simple.SimpleNode())

        # XXX HUGE HACK

        # The problem here is that TextViews calculate and update
        # their size_request in an idle call, or something; I can't
        # figure out a way to have them calculate their size
        # immediately after creation, so I don't know how much room to
        # give them while displaying. I doubt it's possible to do
        # that. So I think the only solution is to give in and just
        # make the layout algorithm incremental, and respond to
        # TextView's size-changing event.

        # XXX This is a huge bug it must be fixed!
        reactor.callLater(0.2, lambda: (self.redisplay(), self.root.widget.grab_focus()))
        self.root.widget.grab_focus()
        # End hack

    def drawLines(self, parent=None):
        if parent is None:
            parent = self.root
        if not parent.expanded: return
        # XXX - make this recursive on the node
        for box in base.INode(parent).getChildren():
            box = base.INodeUI(box)
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
        #print "I AM REDISPLAYING"
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
        self.loadNode(simple.SimpleNode())


    def loadFromXML(self, fn):
        for x in self.canvas.get_children():
            x.destroy()
        root = ctx.call({'controller': self},
                        xmlobject.fromXML, open(fn, 'rb').read())
        self.root = base.INodeUI(root)
        #print "ROOT AM", repr(root.original)
        self.redisplay()


    def loadNode(self, node):
        for x in self.canvas.get_children():
            x.destroy()
        self.root = node
        self.redisplay()


    def on_open_activate(self, thing):

        def _cb_got_filename(button):
            fn = select.get_filename()
            select.destroy()
            self.filename = fn
            self.loadFromXML(fn)

        def _eb_no_filename(button):
            select.destroy()

        select = gtk.FileSelection()
        select.ok_button.connect('clicked', _cb_got_filename)
        select.cancel_button.connect('clicked', _eb_no_filename)
        select.show()

    def _save(self, filename):
        self.filename = filename
        print "dumping", self.root
        tmpfn = filename + '.tmp~~~'
        try:
            f = open(tmpfn, 'w')
            xmlobject.toXML(self.root, f)
            f.close()
        except Exception, e:
            msg = ("There was an error saving your file. :-(\n"
                   "Please report this as a bug. The traceback follows.\n\n")
            io = StringIO()
            import traceback
            traceback.print_exc(file=io)
            msg += io.getvalue()
            md = gtk.MessageDialog(parent=self.window,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_CLOSE,
                                   message_format=msg)
            md.run()
            md.destroy()
        else:
            os.rename(tmpfn, self.filename)


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


