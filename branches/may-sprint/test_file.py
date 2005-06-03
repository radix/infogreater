
from twisted.trial import unittest

from infogreater import ui, xmlobject

from cStringIO import StringIO
import twisted.internet.base
twisted.internet.base.DelayedCall.debug = True

from infogreater.nodes import base, simple

class DummyController(object):
    pass

class DummyCanvas(object):
    def put(*a):
        pass

class TestSave(unittest.TestCase):
    def test_saveEmpty(self):
        controller = DummyController()
        controller.canvas = DummyCanvas()
        nodeui = base.INodeUI(
            simple.makeSimple(controller, content="hello world"))
        savefile = StringIO()
        xmlobject.toXML(nodeui, savefile)
        self.assertEqual(savefile.getvalue(), '<?xml version="1.0"?>\n'
                         '<SimpleNode content="hello world" expanded="True">'
                         '</SimpleNode>')
