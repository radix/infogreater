from twisted.trial import unittest
from infogreater.xmlobject import XMLObject, fromXML, reference, IXMLParent

class ParentyXO(XMLObject):
    contextRemembers = [(IXMLParent, 'parent')]

class XOTest(unittest.TestCase):
    def testIt(self):
        origo = XMLObject(
            {'foo': 'bar'},
            [
            XMLObject({'name': 'chris'}),
            XMLObject({'name': 'armstrong'})
            ]
            )
        origo.children.append(reference(origo))
        origo.children.append(ParentyXO(attrs={'ha': 'qoob'}))

        origx = origo.toXML()

        newo = fromXML(origx)

        self.assertEquals(newo.attrs, origo.attrs)
        self.assertEquals(len(newo.children), len(origo.children))
        self.assertIdentical(newo.children[2].referent, newo)

        newx = newo.toXML()
        self.assertEquals(origx, newx)

    def testParents(self):
        origo = ParentyXO(
            {'foo': 'bar'},
            [
            ParentyXO({'name': 'child'}),
            ]
            )
        origx = origo.toXML()

        newo = fromXML(origx)

        self.assertIdentical(newo.children[0].parent, newo)
