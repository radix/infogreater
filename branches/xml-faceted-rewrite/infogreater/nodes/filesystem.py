from infogreater import facets
from infogreater.nodes import simple

class FileSystemNode(facets.Facet):
    def __init__(self, path='/'):
        self.path = path

    def getChildren(self):
        return [FileSystemNode(path=os.path.join(self.path, path))
                for path in os.listdir(self.path)]

    def getContent(self):
        return self.path


class FileSystemUI(simple.SimpleNodeUI):
    def init(self, controller, parent):
        self.controller = controller
        self.parent = parent
        self._makeWidget()

