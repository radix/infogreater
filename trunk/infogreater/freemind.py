from infogreater import node, ui
from twisted.web import microdom

def freemindToNodes(filename):
    doc = microdom.parseXML(filename)
    top = doc.childNodes[0]
    assert top.tagName == 'map', "This doesn't look like freemind to me!"
    return map(fmn2ign, top.childNodes)

def fmn2ign(fmnode):
    text = fmnode.getAttribute('TEXT')
    print "Text is", text

    n = ui.INodeUI(node.SimpleNode(text))
    children = [fmn2ign(x) for x in fmnode.childNodes if x.tagName == 'node']
    for child in children:
        childbox = ui.INodeUI(child)
        n.childBoxes.append(childbox)
        childbox.parent = n
    n.node.children = children
    return n
        
