import gtk
from twisted.python import components

class IWrappedWidget(components.Interface):
    def toWidget(self):
        """Return the widget that this wraps."""

def toWidget(widget):
    wrap = IWrappedWidget(widget, None)
    if wrap is not None:
        return wrap.toWidget()
    return widget


class CustomWidgetRegister:
    def __init__(self):
        self.widgetTypes = {}
        self.widgets = {}
        
    def register(self, widgetMaker, name=None, *args, **kwargs):
        if name is None:
            name = widgetMaker.__name__
        maker = lambda : widgetMaker(*args, **kwargs)
        self.widgetTypes[name] = maker

    def handler(self, glade, widgetType, widgetName, *args, **kwargs):
        widget = self.widgetTypes[widgetType]()
        self.widgets[widgetName] = widget
        widget = widget.toWidget()
        widget.show()
        return widget

    def getWidget(self, name):
        return self.widgets[name]
        

_theWidgetRegister = CustomWidgetRegister()
registerWrapper = _theWidgetRegister.register
getWrapper = _theWidgetRegister.getWidget

import gtk.glade
gtk.glade.set_custom_handler(_theWidgetRegister.handler)

