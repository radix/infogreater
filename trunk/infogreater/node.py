__metaclass__ = type

from twisted.python import components

class SimpleNode:
    
    def __init__(self, content='', children=None):
        self.content = content
        if children is None:
            children = []
        self.children = children


    def getChildren(self):
        return self.children

    def putChild(self, obj):
        self.children.append(obj)


    def getContent(self):
        return self.content


    def setContent(self, crap):
        self.content = crap

