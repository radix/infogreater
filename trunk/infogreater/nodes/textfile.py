import os

import gtk

from twisted.internet import defer
from twisted.python import context as ctx

from infogreater.nodes import base, simple
from infogreater import facets, xmlobject
from infogreater.nodes.base import INode, INodeUI

class TextFileNode(simple.SimpleNode):

    def __init__(self, original, filename='THIS SUCKS.TXT'):
        simple.SimpleNode.__init__(self, original)
        self.filename = filename
        self.load()


    def setFilename(self, fn):
        self.filename = fn
        self.load()


    def load(self, inf=None):
        print "LOADING", self.filename, "!!!!!!!!"
        if inf is None:
            if os.path.exists(self.filename):
                inf = open(self.filename)
            else:
                return "hell"

        line = inf.readline()
        title = []
        # while we haven't reached a line entirely ====
        while line.strip('=\r\n'):
            title.append(line.rstrip('\r\n'))
            line = inf.readline()
        self.setContent('\n'.join(title))
        assert '=' in line, line

        nodes = {-1: [self]}
        spaces = 0
        for line in inf:
            for char in line:
                if char == ' ':
                    spaces += 1
                else:
                    break


            if not char == '*':
                content = line[spaces:].rstrip('\r\n')
                # theNode is from last iteration
                theNode.setContent(theNode.getContent() + '\n' + content)
            else:
                content = line[spaces+2:].rstrip('\r\n')
                level = (spaces - 1) / 2
                parent = INode(nodes[level - 1][-1])
                theNode = INode(
                    simple.makeSimple(INodeUI(self).controller,
                                      parent=parent,
                                      content=content))
                nodes.setdefault(level, []).append(theNode)
                parent.children.append(theNode)
            spaces = 0
            level = 0


    def writeNode(self, outf, content, spaces):
        lines = content.splitlines()
        outf.write(' '*spaces + ' * ' + lines[0] + '\n')
        for line in lines[1:]:
            outf.write(' '*spaces + '   ' + line + '\n')

    def save(self, outf=None):
        if outf is None:
            outf = open(self.filename, 'w')
        # XXX support newlines!
        outf.write(self.content + '\n')
        # write out as many =s as the longest line of the title
        outf.write('='*max(map(len, self.content.splitlines())) + '\n')
        return self._save(outf, self.children, 0)


    def _save(self, outf, children, level):
        for x in children:
            self.writeNode(outf, x.content, 2*level)
            self._save(outf, x.children, level+1)


def getFileName(glob='*'):
    d = defer.Deferred()

    fs = gtk.FileSelection()
    fs.complete(glob)
    fs.ok_button.connect('clicked',
                         lambda a: d.callback(fs.get_filename()))
    fs.cancel_button.connect('clicked',
                             lambda a: d.errback(Exception("Cancelled")))
    fs.show_all()
    d.addBoth(lambda r: (fs.destroy(), r)[1])
    return d


class TextFileUI(simple.SimpleNodeUI):

    def _cbPopup(self, textview, menu):
        print "adding MI!"
        mi = gtk.MenuItem('save to %s' % (INode(self).filename,))
        mi.connect('activate', self._cbSave)
        menu.append(mi)
        menu.show_all()

    def _cbSave(self, mi):
        print "Saving!"
        INode(self).save()


class TextNodeXML(base.BaseNodeXML):
    # Relying on order of bases here to say that __init__ comes from
    # Facet and ignore XMLObject's __init__
    tagName = 'TextFile'

    def getAttrs(self):
        nodeui = INodeUI(self)
        node = INode(self)
        return {'expanded': str(nodeui.expanded),
                'filename': node.filename}

    def getChildren(self):
        # The children get persisted to the text file.
        return []


    def setXMLState(self, attrs, children, parent):
        node = INode(self)
        node.parent = INode(parent, None)

        nodeui = INodeUI(self)
        nodeui.expanded = attrs['expanded'] == "True"
        nodeui.controller = ctx.get('controller')

        node.setFilename(attrs['filename'])
        nodeui._makeWidget()

def makeTextBase():
    faced = facets.Faceted()
    faced[INode] = TextFileNode(faced)
    faced[INodeUI] = TextFileUI(faced)
    faced[xmlobject.IXMLObject] = TextNodeXML(faced)
    #faced[facets.IReprable] = INode(faced)
    return faced

# XXX Use plugins or context something
xmlobject.unmarmaladerRegistry['TextFile'] = makeTextBase

def makeText(controller):
    textnode = makeTextBase()
    nodeui = INodeUI(textnode)
    nodeui.controller = controller
    nodeui._makeWidget()
    node = INode(textnode)

    d = getFileName('*.txt')
    d.addCallback(node.setFilename)

    return textnode
