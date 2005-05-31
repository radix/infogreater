
from twisted.trial import unittest
from twisted.python import context

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple
from infogreater.wrapper import SimpleNodeWrapper

from test_framework import DummyController, DummyCanvas

class TestWrap(unittest.TestCase):
    def test_stupid(self):
        controller = DummyController()
	node = simple.makeSimple(controller, content="stupid")
	stupid = SimpleNodeWrapper(node)
        self.assertEqual(stupid.getContent(), 'stupid')
        self.failIf(stupid.hasChildren())

class TestSave(unittest.TestCase):
    def test_saveTiny(self):
        controller = DummyController()
        node = base.INode(
            simple.makeSimple(controller, content="hello world"))
        savefile = StringIO()
        xmlobject.toXML(node, savefile)
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

