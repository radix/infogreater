from infogreater import node
from twisted.web import microdom

def freemindToNodes(filename):
    doc = microdom.parseXML(filename)
    top = doc.childNodes[0]
    assert top.tagName == 'map', "This doesn't look like freemind to me!"
    return map(fmn2ign, top.childNodes)

def fmn2ign(fmnode):
    text = fmnode.getAttribute('TEXT')
    print "Text is", text
    n = node.SimpleNode(text,
                        [fmn2ign(x) for x in fmnode.childNodes if x.tagName == 'node'])
    return n
        
