
from twisted.trial import unittest
from twisted.python import context

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple

from test_framework import DummyController, DummyCanvas

class TestXmlFormat(unittest.TestCase):
    def test_toXML(self):
        controller = DummyController()
        nodeA = base.INode(
            simple.makeSimple(controller, content="apple"))
        nodeB = base.INode(
            simple.makeSimple(controller, content="banana"))
        nodeA.setChildren([nodeB])
        nodeB.addParent(nodeA)

        expected = ('<?xml version="1.0"?>\n'
                    '<SimpleNode content="apple" expanded="True">'
                    '<SimpleNode content="banana" expanded="True">'
                    '</SimpleNode>'
                    '</SimpleNode>')

        self.assertEqual(xmlobject.toXMLString(nodeA), expected)
