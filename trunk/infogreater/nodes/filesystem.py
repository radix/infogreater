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


    def hasChildren(self):
        return os.path.isdir(self.path)


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
    faced[INodeUI] = base.DynamicCachingNodeUI(faced)
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
