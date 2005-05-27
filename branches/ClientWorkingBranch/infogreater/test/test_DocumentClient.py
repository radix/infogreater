from infogreater import DocumentClient

from twisted.trial import unittest
from twisted.spread import pb
from twisted.internet import reactor
from twisted.cred.portal import IRealm
from twisted.cred.portal import Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse

class DocServerTests(unittest.TestCase):
    class SimpleRealm:
        __implements__ = IRealm
        def __init__(self, test_class):
            self.test_case = test_class
            
        def requestAvatar(self, avatarId, mind, *interfaces):
            if pb.IPerspective in interfaces:
                avatar = pb.Avatar()
                self.test_case.avatars.append(avatar)
                return pb.IPerspective, avatar, None
            else:
                raise NotImplementedError("no interface")
    
    def setUp(self):
        self.avatars = list()
    
    def _onLogin(self, conn):
        conn.broker.transport.loseConnection()
        assert not self.avatars.is_empty()
    
    def _onLoginFail(self, conn):
        conn.broker.transport.loseConnection()
        assert not self.avatars.is_empty()
        assert False
    
    def testClientConnects(self):
        self.portal = Portal(self.SimpleRealm(self))
        self.checker = InMemoryUsernamePasswordDatabaseDontUse()
        self.checker.addUser("guest", "guest")
        self.portal.registerChecker(self.checker)
        self.factory = pb.PBServerFactory(self.portal)
        self.listener = reactor.listenTCP(pb.portno, self.factory)
        self.client = DocumentClient.Client()
        return self.client.connect("localhost").addCallbacks(self._onLogin, self._onLoginFail)
    
    def tearDown(self):
        self.listener.stopListening()
