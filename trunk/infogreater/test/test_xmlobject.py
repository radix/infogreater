from twisted.trial import unittest
from infogreater.xmlobject import XMLObject

class SomeSubclass(XMLObject):
    pass

class ThingyTest(unittest.TestCase):
    def testIt(self):
        origo = XMLObject({'foo': 'bar'},
                       [
                       XMLObject({'name': 'chris'}),
                       XMLObject({'name': 'armstrong'})
                       ]
                       )
        origo.children.append(origo)
        origo.children.append(SomeSubclass(attrs={'ha': 'qoob'}))

        origx = origo.toXML()
        
        newo = XMLObject.fromXML(origx)

        self.assertEquals(newo.attrs, origo.attrs)
        self.assertEquals(len(newo.children), len(origo.children))
        self.assertIdentical(newo.children[2], newo)

        newx = newo.toXML()
        self.assertEquals(origx, newx)
