from sets import Set as set

class MultiNode(facets.Facet):
    """This class exists to be the parent of DigraphNode"""

    def __init__(self, nodes):
    	self.nodes = nodes

    def getParent(self):
    	MultiNode(list(set(
            reduce(append, [node.getParent().getNodes() for node in self.nodes], [])
	)))

    def getNodes(self):
    	return self.nodes

    def getContent(self):
        assert("can't getContent on a MultiNode")

    def setContent(self):
        assert("can't setContent on a MultiNode")

    def getChildren(self):
        list(set(
            reduce(append, [node.getChildren() for node in self.nodes], [])
	))

