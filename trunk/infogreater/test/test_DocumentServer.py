from infogreater import DocumentServer

from twisted.trial import unittest
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
from twisted.internet import reactor

class DocServerTests(unittest.TestCase):
    def success(self, login_value):
        self.succeeded = True
    
    def fail(self, login_value):
        assert False
    
    def tearDown(self):
        self.server.shutDown()
        self.connector.disconnect()
        self.factory.disconnect()
        for i in xrange(10):
            reactor.iterate()
    
    def testServerListens(self):
        self.server = DocumentServer.Server()
        self.factory = pb.PBClientFactory()
        self.connector = reactor.connectTCP("localhost", pb.portno,
                                            self.factory)
        return self.factory.login(UsernamePassword("guest", "guest")
                                  ).addCallbacks(self.success, self.fail)
