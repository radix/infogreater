import sys
from cStringIO import StringIO

from twisted.trial import unittest
from infogreater.node import SimpleNode, TextFileNode

class FileNodeTest(unittest.TestCase):
    def testSaveAndLoad(self):
        tn = TextFileNode("Foorg.txt")
        tn.setContent("The TEXT file of DOOM.")

        p1 = SimpleNode("Point ONE.")
        tn.putChild(p1)
        p1.putChild(SimpleNode("I am CHRIS."))
        p1.putChild(SimpleNode("I am ARMSTRONG."))

        p2 = SimpleNode("Point 2.")
        tn.putChild(p2)
        skinny = SimpleNode("I am RADIX.")
        p2.putChild(skinny)
        skinny.putChild(SimpleNode("Yeah, pretty RAD."))
        p2.putChild(SimpleNode("And I'm made out of poison."))


        io = StringIO()
        tn.save(io)
        FIRST = io.getvalue()
        io.seek(0)
        tn2 = TextFileNode('ueoa')
        tn2.load(io)

        io = StringIO()
        tn2.save(io)
        SECOND = io.getvalue()
        self.assertEquals(FIRST, SECOND)

    def testFromString(self):
        content = """The TEXT file of DOOM.
======================
 * Point ONE.
   * I am CHRIS.
   * I am ARMSTRONG.
 * Point 2.
   * I am RADIX.
     * Yeah, pretty RAD.
   * And I'm made out of poison.
"""
        tn = TextFileNode("blargho")
        tn.load(StringIO(content))
        io = StringIO()
        tn.save(io)
        self.assertEquals(io.getvalue(), content)

    def testNewLines(self):
        content = """The TEXT file of DOOM.
WITH A FRIGGIN' NEWLINE
=======================
 * Point ONE.
   * I am CHRIS
     JACOB.
   * I am ARMSTRONG.
 * Point 2.
   * I am RADIX.
     * Yeah, pretty RAD.
   * And I'm made out of poison.
"""     
        tn = TextFileNode("blargho")
        tn.load(StringIO(content))
        io = StringIO()
        tn.save(io)
        self.assertEquals(io.getvalue(), content)        


