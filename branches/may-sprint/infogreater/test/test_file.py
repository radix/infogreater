
from twisted.trial import unittest
from twisted.python import context

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple

class DummyController(object):
    def __init__(self):
        self.canvas = DummyCanvas()
        
class DummyCanvas(object):
    def put(*a):
        pass

class TestSave(unittest.TestCase):
    def test_saveTiny(self):
        controller = DummyController()
        nodeui = base.INodeUI(
            simple.makeSimple(controller, content="hello world"))
        savefile = StringIO()
        xmlobject.toXML(nodeui, savefile)
        self.assertEqual(savefile.getvalue(), '<?xml version="1.0"?>\n'
                         '<SimpleNode content="hello world" expanded="True">'
                         '</SimpleNode>')

    def test_restoreTiny(self):
        controller = DummyController()
        root = context.call({'controller': controller},
                            xmlobject.fromXML, '<?xml version="1.0"?>\n'
                            '<SimpleNode content="hi there" expanded="True">'
                            '</SimpleNode>')
        root = base.INode(root)
        self.assertEqual(root.getContent(), "hi there")
        self.failIf(root.hasChildren())
