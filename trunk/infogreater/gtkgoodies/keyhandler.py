import gtk
from gtk import keysyms

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
