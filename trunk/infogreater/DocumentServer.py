from twisted.spread import pb
from twisted.cred.portal import IRealm
from twisted.internet import reactor
from twisted.cred.portal import Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse

class DefinedError(pb.Error):
    pass

class SimplePerspective(pb.Avatar):
    def perspective_echo(self, text):
        print 'echoing',text
        return text

    def perspective_error(self):
        raise DefinedError("exception!")

    def logout(self):
        pass

class SimpleRealm:
    __implements__ = IRealm

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            avatar = SimplePerspective()
            return pb.IPerspective, avatar, avatar.logout
        else:
            raise NotImplementedError("no interface")

class Server(object):
    def __init__(self):
        self.portal = Portal(SimpleRealm())
        self.checker = InMemoryUsernamePasswordDatabaseDontUse()
        self.checker.addUser("guest", "guest")
        self.portal.registerChecker(self.checker)
        self.factory = pb.PBServerFactory(self.portal)
        self.listener = reactor.listenTCP(pb.portno, self.factory)
    
    def shutDown(self):
        self.listener.stopListening()
