__metaclass__ = type

from twisted.python import components

class SimpleNode:

    def __init__(self, content=''):
        self.content = content
        self.children = []

    def getChildren(self):
        return self.children

    def putChild(self, obj):
        self.children.append(obj)

    def getContent(self):
        return self.content

    def setContent(self, crap):
        self.content = crap


    def __str__(self):
        return "<%s content=%r children=%r>" % (self.__class__, self.content, self.children)
    __repr__ = __str__

import os

class TextFileNode(SimpleNode):

    def __init__(self, filename):
        SimpleNode.__init__(self)
        self.filename = filename
        self.load()


    def __getstate__(self):
        d = self.__dict__.copy()
        del d['content']
        del d['children']

    def __setstate__(self, d):
        self.__dict__ = d
        self.load()


    def load(self, inf=None):
        if inf is None:
            if os.path.exists(self.filename):
                inf = open(self.filename)
            else:
                return "hell"

        title = inf.readline().rstrip('\r\n')
        self.setContent(title)
        bloo = inf.readline()
        assert "=" in bloo, repr(bloo) # line of "==="

        nodes = {-1: [self]}
        spaces = 0
        for line in inf:
            for char in line:
                if char == ' ':
                    spaces += 1
                else:
                    break
            assert char == '*'
            content = line[spaces+2:].rstrip('\r\n')
            level = (spaces - 1) / 2
            theNode = SimpleNode(content)
            nodes.setdefault(level, []).append(theNode)
            nodes[level - 1][-1].putChild(theNode)
            spaces = 0
            level = 0


    def save(self, outf=None):
        if outf is None:
            outf = open(self.filename, 'w')
        # XXX support newlines!
        outf.write(self.content.replace('\n', '|') + '\n')
        outf.write('='*len(self.content) + '\n')
        return self._save(outf, self.children, 0)


    def _save(self, outf, children, level):
        for x in children:
            outf.write('  '*level + ' * ' + x.content + '\n')
            self._save(outf, x.children, level+1)
        
if __name__ == '__main__':
    tn = TextFileNode("Foorg.txt")
    tn.setContent("The TEXT file of DOOM.")

    p1 = SimpleNode("Point ONE.")
    tn.putChild(p1)
    p1.putChild(SimpleNode("I am CHRIS."))
    p1.putChild(SimpleNode("I am ARMSTRONG."))

    p2 = SimpleNode("Point 2.")
    tn.putChild(p2)
    skinny = SimpleNode("I am Skinny.")
    p2.putChild(skinny)
    skinny.putChild(SimpleNode("Yeah, pretty skinny."))
    p2.putChild(SimpleNode("And I'm 5'11."))

    from cStringIO import StringIO
    io = StringIO()
    tn.save(io)
    FIRST = io.getvalue()
    print FIRST
    io.seek(0)
    tn2 = TextFileNode('ueoa')
    tn2.load(io)
    import sys
    io = StringIO()
    tn2.save(io)
    SECOND = io.getvalue()
    print SECOND
    assert FIRST == SECOND
    print "PASS"

