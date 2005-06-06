
from infogreater.nodes import base

class SimpleNodeWrapper(object):
    '''Wrap a data structure with responses for the UI'''

    def __init__(self, node):
        self._node = base.INode(node)

    def getContent(self):
        return self._node.getContent()

    def hasChildren(self):
        return self._node.hasChildren()

    def listen(self, what):
        assert what not in self.registered
	self.registered.append(what)

    def shutup(self, what):
	self.registered.remove(what)

    def changed(self):
        for what in self.registered:
	    what(self)

