import sys
from xml.dom import minidom

def freemindToNodes(filename):
    doc = minidom.parse(filename)
    top = doc.childNodes[0]
    assert top.tagName == 'map', "This doesn't look like freemind to me!"
    return filter(None, map(fmn2ign, top.childNodes))

def fmn2ign(fmnode):
    if isinstance(fmnode, minidom.Text) and fmnode.data.isspace():
        return None
    text = fmnode.getAttribute('TEXT')#.replace('&#xa;', '\n')
    print >> sys.stderr, "TEXT", repr(text)
    node = minidom.Element('SimpleNode')
    for attr,v in [('content', text),
                   ('expanded', 'False')]:
        node.setAttribute(attr,v)

    children = filter(None,
                      [fmn2ign(x)
                       for x in fmnode.childNodes if x.nodeName == 'node'])
    node.childNodes = children
    return node

if __name__ == '__main__':
    print freemindToNodes(sys.argv[1])[0].toprettyxml()
