import os

from infogreater import facets, xmlobject
from infogreater.nodes import base
from infogreater.nodes.base import INode, INodeUI

class FileSystemNode(facets.Facet):
    def __init__(self, original, path='/'):
        facets.Facet.__init__(self, original)
        self.path = path

    def getChildren(self):
        return [makeFileSystem(controller=INodeUI(self).controller,
                               parent=self,
                               path=os.path.join(self.path, path))
                for path in os.listdir(self.path)]

    def getContent(self):
        return self.path

# XXX I really ought to be subclassing a "DynamicCachingUI" or
# something
class FileSystemUI(base.BaseNodeUI):
    expanded = False
    def __init__(self, *a, **kw):
        self._cacheChildren = []
        base.BaseNodeUI.__init__(self, *a, **kw)

    def hasChildren(self):
        return os.path.isdir(INode(self).path)

    def placedUnder(self, parent):
        INode(self).parent = INode(parent)
        self._makeWidget()

    def uichildren(self):
        return self._cacheChildren

    def showChildren(self):
        children = INode(self).getChildren()
        self._cacheChildren = [INodeUI(x) for x in children]
        base.BaseNodeUI.showChildren(self)

    def hideChildren(self):
        base.BaseNodeUI.hideChildren(self)
        for x in self._cacheChildren:
            x.destroyChildren()
        self._cacheChildren = []

class FileSystemXML(base.BaseNodeUI):
    tagName = 'FileSystem'

    def getAttrs(self):
        nodeui = INodeUI(self)
        node = INode(self)
        return {'expanded': str(nodeui.expanded),
                'path': node.path}

    def getChildren(self):
        return []

    def setXMLState(self, attrs, children, parent):
        node = INode(self)
        node.parent = INode(parent, None)

        nodeui = INodeUI(self)
        nodeui.expanded = attrs['expanded'] == "True"
        nodeui.controller = ctx.get('controller')

        node.path = attrs['filename']
        nodeui._makeWidget()
        
def makeFileSystemBase(path='/'):
    faced = facets.Faceted()
    faced[INode] = FileSystemNode(faced, path)
    faced[INodeUI] = FileSystemUI(faced)
    faced[xmlobject.IXMLObject] = FileSystemXML(faced)
    #faced[facets.IReprable] = INode(faced)
    return faced

def makeFileSystem(controller, parent=None, path='/'):
    fsnode = makeFileSystemBase(path=path)
    nodeui = INodeUI(fsnode)
    nodeui.controller = controller
    nodeui._makeWidget()
    node = INode(fsnode)
    node.parent = parent
    return fsnode
