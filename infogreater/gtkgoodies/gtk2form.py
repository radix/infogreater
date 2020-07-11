"""

If you want to override how a particular type of Typed or Binding is
rendered, use

  twisted.python.context.callWithContext(
      {components.AdapterRegistry: myRegistry},
      IBindingWidget, myBinding)

Whre 'myRegistry' is an AdapterRegistry instance that you've set up to
give different adapters for particular Typeds or Bindings to
ITypedWidget or IBindingWidget.

"""



import gtk

from twisted.python import components
from twisted.python.components import getInterfaces

from twisted.internet import defer

from nevow import formless
from nevow.formless import TypedInterface




################
## Binding stuff
################

class IBindingWidget(components.Interface):
    """
    Knows how to render a Binding.
    """
    widget = property(doc="A L{gtk.Widget}")


class MethodBindingWidget(components.Adapter):
    __implements__ = (IBindingWidget,)
    def getWidget(self, configurable, deferred):
        vb = gtk.VBox()

        typedwidgets = []
        def act():
            values = [
                arg.typedValue.coerce(tw.getValue()) for arg,tw in typedwidgets
                ]
            m = getattr(configurable, self.original.name)
            try:
                # [:-1] is a *terrible* hack: formless sticks a Submit
                # button in the return value of getArgs when the
                # binding doesn't specify any other Buttons. It
                # *shouldn't* do this: it's lying about what arguments
                # the function will accept. It should rely on the user
                # interface-generater (like freeform and gtk2form) to
                # handle the case where no buttons are specified. That
                # way I can know whether or not a button should really
                # produce an argument to the method.
                deferred.callback(m(*values[:-1]))
            except:
                deferred.errback()

        for arg in self.original.getArgs():
            tw = ITypedWidget(arg.typedValue)
            typedwidgets.append((arg, tw))
            vb.pack_start(tw.getWidget(arg.name, act), True, True, 0)

        return vb


components.registerAdapter(MethodBindingWidget, formless.MethodBinding, IBindingWidget)



##############
## Typed stuff
##############

class ITypedWidget(components.Interface):
    """
    Knows how to render a single Typed.
    """
    def getWidget(self, name, act):
        """
        return a widget!
        """

    def getValue(self):
        """
        Return the value that the user gave.
        """

class EntryWidget(components.Adapter):
    __implements__ = (ITypedWidget,)
    def getWidget(self, name, act):
        hb = gtk.HBox()
        if self.original.label:
            name = self.original.label
        l = gtk.Label(name)
        l.show()
        hb.pack_start(l, True, True, 0)

        self.entry = entry = gtk.Entry()
        entry.set_text(self.original.default)
        hb.pack_start(entry, True, True, 0)

        return hb

    def getValue(self):
        return self.entry.get_text()

components.registerAdapter(EntryWidget, formless.String, ITypedWidget)
components.registerAdapter(EntryWidget, formless.Integer, ITypedWidget)

class ButtonWidget(components.Adapter):
    __implements__ = (ITypedWidget,)
    def getWidget(self, name, act):
        but = gtk.Button(self.original.label)
        but.connect('clicked', lambda *args: act())
        return but

    def getValue(self):
        return True

components.registerAdapter(ButtonWidget, formless.Button, ITypedWidget)



def configure(o, typediface, name):
    """
    @param o: Something that implements L{typediface}.
    @param typediface: A subclass of L{freeform.TypedInterface}.
    @param name: The name of a binding specified by L{typediface}.
    @returns: An L{IBindingWidget}. Access its 'widget' attribute to get a
              gtk widget you can stick somewhere.
    """
    for binding in typediface.__spec__:
        if binding.name == name:
            break
    else:
        raise ValueError("Couldn't find %s.%s in %r" % (typediface.__name__, name, o))
    d = defer.Deferred()
    widget = IBindingWidget(binding).getWidget(o, d)
    return widget, d


def menu(o, cb):
    """
    I return a L{gtk.HBox} containing buttons that, when clicked,
    display a dialog containing a form. When a form is submitted, its
    dialog will be destroyed and the callback you passed in will be
    called.
    """
    hb = gtk.HBox()

    nonstupid = lambda x: (issubclass(x, TypedInterface)
                           and x is not TypedInterface)
    for iface in [iface for iface in getInterfaces(o) if nonstupid(iface)]:
        print "iface", iface
        for binding in iface.__spec__:
            print "binding", binding
            def makeDialog(button, binding=binding):
                win = gtk.Window()
                win.set_title(binding.name)
                d = defer.Deferred()
                def whenDone(r):
                    win.destroy()
                    cb()
                d.addBoth(whenDone)
                win.add(IBindingWidget(binding).getWidget(o, d))
                win.show_all()
            b = gtk.Button(binding.name)
            b.connect('clicked', makeDialog)
            b.show()
            hb.pack_start(b, True, True, 0)
    hb.show_all()
    return hb


def disp_childs(w):
    for x in w.get_children():
        print x
        if hasattr(x, 'get_children'):
            disp_childs(x)


if __name__ == '__main__':
    class IFoo(formless.TypedInterface):
        def add(self):#, thing=formless.String(), thing2=formless.String(), thing3=formless.Integer()):
            pass
        add = formless.autocallable(add)

    class Boo:
        __implements__ = (IFoo,)
        def add(self):#, thing, thing2, thing3):
            print "OMG OMG OMG OMG OMG"#, thing, thing2
            

    widg, d = configure(Boo(), IFoo, 'add')
    d.addBoth(gtk.mainquit)

    win = gtk.Window()
    win.add(widg)
#    win.show()
    win.show_all()
##    print "=============="
##    disp_childs(win)
##    print "--------------"
    gtk.main()

