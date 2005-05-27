from infogreater import DocumentServer

from twisted.trial import unittest
from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
from twisted.internet import reactor

class DocServerTests(unittest.TestCase):
    def _onConnect(self, connection):
        connection.broker.transport.loseConnection()
    
    def _onConnectFail(self, connection):
        connection.broker.transport.loseConnection()
        assert False
    
    def tearDown(self):
        self.server.shutDown()
        self.connector.disconnect()
        self.factory.disconnect()
    
    def testServerListens(self):
        self.server = DocumentServer.Server()
        self.factory = pb.PBClientFactory()
        self.connector = reactor.connectTCP("localhost", pb.portno, self.factory)
        return self.factory.login(UsernamePassword("guest", "guest")) \
            .addCallbacks(self._onConnect, self._onConnectFail)
