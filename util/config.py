import configparser

class Config:
    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.file = filename
        self.token = None
        self.prefix = None
        self.ownerid = None
        self.errorserver = None
        self.errorchannel = None
        self.successful = False

    def read(self):
        try:
            self.config.read(self.file)
            self.token = self.config["Login"]["Token"]
            self.prefix = self.config["DEFAULT"]["Prefix"]
            self.ownerid = self.config["ErrorHandler"]["OwnerID"]
            self.errorserver = self.config["ErrorHandler"]["ServerID"]
            self.errorchannel = self.config["ErrorHandler"]["ChannelID"]
            self.successful = True
        except:
            self.successful = False