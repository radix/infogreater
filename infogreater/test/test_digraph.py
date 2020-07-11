
from twisted.trial import unittest
from twisted.python import context

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple

from test_framework import DummyController, DummyCanvas

class TestDigraph(unittest.TestCase):
    def makeCycle(self):
        controller = DummyController()
        nodeA = base.INode(simple.makeSimple(controller, content="apple"))
        nodeB = base.INode(simple.makeSimple(controller, content="banana"))
        nodeC = base.INode(simple.makeSimple(controller, content="carrot"))
        
        nodeB.addParent(nodeA)
        nodeA.setChildren([nodeB])
        
        nodeC.addParent(nodeB)
        nodeB.setChildren([nodeC])

        nodeA.addParent(nodeC)
        nodeC.setChildren([nodeA])

        return nodeA

    def test_cycle(self):
        x = self.makeCycle()
        assert(x.getChildren()[0].getChildren()[0].getChildren()[0] is x)

    def test_cycleSave(self):
        cycleHead = self.makeCycle()
        savefile = StringIO()
        xmlobject.toXML(cycleHead, savefile)
        assert(len(savefile.getvalue()) < 1000000)
    test_cycleSave.skip = "XMLObject doesn't support implicit references"

