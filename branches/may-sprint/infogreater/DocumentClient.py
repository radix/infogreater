from twisted.spread import pb
from twisted.cred.credentials import UsernamePassword
from twisted.internet import reactor

class Client:
    def __init__(self):
        self.factory = pb.PBClientFactory()

    def connect(self, hostname):
        self.connector = reactor.connectTCP(hostname, pb.portno, self.factory)
        return self.factory.login(UsernamePassword("guest", "guest")) 
