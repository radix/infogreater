from twisted.trial import unittest
from infogreater.xmlobject import XMLObject, fromXML, toXMLString, reference, IXMLParent
from infogreater import xmlobject

class ParentyXO(XMLObject):
    contextRemembers = [(IXMLParent, 'parent')]

class XOTest(unittest.TestCase):
    def setUp(self):
        xmlobject.unmarmaladerRegistry['XMLObject'] = XMLObject
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

        origx = toXMLString(origo)

        newo = fromXML(origx)

        self.assertEquals(newo.attrs, origo.attrs)
        self.assertEquals(len(newo.children), len(origo.children))
        self.assertIdentical(newo.children[2].referent, newo)

        newx = toXMLString(newo)
        self.assertEquals(origx, newx)

    def testParents(self):
        origo = ParentyXO(
            {'foo': 'bar'},
            [
            ParentyXO({'name': 'child'}),
            ]
            )
        origx = toXMLString(origo)

        newo = fromXML(origx)

        self.assertIdentical(newo.children[0].parent, newo)
