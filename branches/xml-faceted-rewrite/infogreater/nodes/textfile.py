import os

from infogreater.nodes import simple

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


class TextFileNode(simple.SimpleNode):

    def __init__(self, filename='THIS SUCKS.TXT'):
        SimpleNode.__init__(self)
        self.filename = filename
        self.load()


    def setFilename(self, fn):
        self.filename = fn
        self.load()

    def __getstate__(self):
        d = self.__dict__.copy()
        del d['content']
        del d['children']
        return d

    def __setstate__(self, d):
        self.__dict__ = d
        self.content = ""
        self.children = []
        self.load()


    def load(self, inf=None):
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
                theNode = SimpleNode(content)
                nodes.setdefault(level, []).append(theNode)
                nodes[level - 1][-1].putChild(theNode)
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


class TextFileUI(simple.SimpleNodeUI):
    def init(self, controller, parent):
        print "HEY GETTING FILENAME"
        d = getFileName('*.txt')
        def gotIt(r):
            self.original.setFilename(r)
        d.addCallback(gotIt)
        simple.SimpleNodeUI.init(self, controller, parent)

    def _cbPopup(self, textview, menu):
        print "adding MI!"
        mi = gtk.MenuItem('save to %s' % (self.original.filename,))
        mi.connect('activate', self._cbSave)
        menu.append(mi)
        menu.show_all()

    def _cbSave(self, mi):
        print "Saving!"
        self.original.save()