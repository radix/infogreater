import gtk, gobject
from twisted.python import reflect, components
from infogreater.gtkgoodies import wrap

class List:
    """Provides a simple interface for dealing with the most common use-cases
    for a GTK+ 2 list widget. Namely creation, addition of rows, and retrieval
    (including retrieval of selected rows) in a table.
    """

    __implements__ = wrap.IWrappedWidget
    
    def __init__(self, view, columns, columnRenderers=None):
        """Constructor. Specify the TreeView widget and a list describing the
        columns of the table, in addition to any non-standard cell renderers
        that you may require.

        @param view: The TreeView widget we are wrapping.
        @ptype view: gtk.TreeView
        @param columns: A list describing the columns of the table.
        @ptype columns: list [('Column Title', <gtktype>)]
            where gtktype is the type of the object. Normally the python type
            (e.g. str, int) is acceptable, but occasionally (notably for bools)
            the gobject type (e.g. gobject.TYPE_BOOLEAN) is required.
        @param columnRenderers: A dict describing renderers for non-text
        columns.
        @ptype columnRenderers:
           { 'Column Title': (renderer, position, properties) }
           renderer: Instance of L{gtk.CellRenderer} subclass
           position: String describing where to store data. e.g. 'text' for a
                     text cell renderer.
           attributes: A dict of attributes for the rendering of the column
           properties: A dict of properties to give to L{gtk.CellRenderer}
                       instance. Consult gtk documentation for details.
        """
        columnRenderers = columnRenderers or {}
        boolShield = lambda x : (x is bool) and gobject.TYPE_BOOLEAN or x
        self.store = self._createStore(*[boolShield(column[1]) for column in columns])
        c = []
        for i, (name, _) in enumerate(columns):
            data = columnRenderers.get(name, (gtk.CellRendererText(),
                                              'text', {}, {}))
            if data is None:
                continue
            renderer, position, attributes, properties = data
            attributes[position] = i
            column = gtk.TreeViewColumn(name, renderer, **attributes)
            c.append(column)
            for item in properties.iteritems():
                renderer.set_property(*item)
        map(view.append_column, c)
        self.columns = [column[0] for column in columns]
        view.set_model(self.store)
        self.view = view

    def _createStore(self, *args):
        return gtk.ListStore(*args)

    def toWidget(self):
        return self.view

    def add(self, values, iter=None):
        """Adds a row to the table. Also provides for editing rows in the table.

        @param values: A list of tuples of column names and values for those
        columns
        @ptype values: [('Column Title', value), ...]
        @param iter: Option value. Tells C{add} which row to edit. If not
        specified, C{add} will create a new row.
        @ptype iter: L{gtk.TreeIter}
        @return: L{gtk.TreeIter} of newly created row.
        """
        if iter is None:
            iter = self.store.append()
        return self.set(values, iter)

    def set(self, values, iter):
        args = []
        for i, title in enumerate(self.columns):
            value = values.get(title, None)
            if value is not None:
                args.extend([i, value])
        self.store.set(iter, *args)
        return iter

    def clear(self):
        """Remove all rows from the table.
        """
        self.store.clear()

    def __len__(self):
        return len(self.store)

    def get(self, iter):
        """Retrieve the values of the row with the given iteration reference.
        @param iter: Reference to row in model.
        @ptype iter: L{gtk.TreeIter}
        @return: dict. { 'Column Title': value, ... }
        """
        return dict([(title, self.store[iter][i])
                          for i, title in enumerate(self.columns)])

    def getSelection(self):
        """Returns the values of the currently selected row.
        @return: dict. { 'Column Title': value, ... }
        """
        iter = self.view.get_selection().get_selected()[1]
        if iter is None:
            raise ValueError("no selection")
        return self.get(iter)


class Tree(List):
    """Example code:
    | def foo():
    |     window = gtk.Window()
    |     tree = tree.Tree(gtk.TreeView(), [('Name', str), ('Value', str)])
    |     window.add(wrap.toWidget(tree))
    |     window.show_all()
    |     button = tree.add(dict(Name='Button', Value='Aardvark'))
    |     tree.add(dict(Name='Humphrey', Value='Bilby'), button)
    |     tree.add(dict(Name='Anna', Value='Cassowary'), button)
    |     widget = tree.add(dict(Name='Widget', Value='Dingo'))
    |     tree.add(dict(Name='Livia', Value='Emu'), widget)
    |     tree.add(dict(Name='Plurabelle', Value='Goanna'), widget)
    """

    __implements__ = wrap.IWrappedWidget
   
    def _createStore(self, *args):
        return gtk.TreeStore(*args)

    def add(self, values, parent=None):
        return self.set(values, self.store.append(parent))

def pixbufRender():
    return (gtk.CellRendererPixbuf(), 'pixbuf', {}, {})

