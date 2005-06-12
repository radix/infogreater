
from twisted.trial import unittest
from twisted.python import context

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple

from test_framework import DummyController, DummyCanvas

class TestXmlFormat(unittest.TestCase):
    def test_ToString(self):
        controller = DummyController()
        nodeA = base.INode(
            simple.makeSimple(controller, content="apple"))
        nodeB = base.INode(
            simple.makeSimple(controller, content="banana"))
        nodeA.setChildren([nodeB])
        nodeB.addParent(nodeA)

        self.assertEqual(
            str(nodeA),
            '<?xml version="1.0"?>\n'
            '<SimpleNode content="apple" id="1" expanded="True">'
            '</SimpleNode>'
            '<SimpleNode content="banana" id="2" expanded="True">'
            '</SimpleNode>'
            '<SimpleEdge start="1" end="2">'
            '</SimpleEdge>')
