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
        self.customcmd_timeout = 0
        self.essential_timeout = 0
        self.gameReady_timeout = 0
        self.gameRound_timeout = 0
        self.link_timeout = 0
        self.random_timeout = 0
        self.search_timeout = 0
        self.generic_timeout = 0
        self.successful = False

    def read(self):
        try:
            self.config.read(self.file)
            self.token = self.config["Login"]["Token"]
            self.prefix = self.config["DEFAULT"]["Prefix"]
            self.ownerid = self.config["ErrorHandler"]["OwnerID"]
            self.errorserver = self.config["ErrorHandler"]["ServerID"]
            self.errorchannel = self.config["ErrorHandler"]["ChannelID"]
            self.customcmd_timeout = self.config["Timeout"].getint("Customcmd")
            self.essential_timeout = self.config["Timeout"].getint("Essential")
            self.gameReady_timeout = self.config["Timeout"].getint("GameReady")
            self.gameRound_timeout = self.config["Timeout"].getint("GameRound")
            self.link_timeout = self.config["Timeout"].getint("Link")
            self.random_timeout = self.config["Timeout"].getint("Random")
            self.search_timeout = self.config["Timeout"].getint("Search")
            self.generic_timeout = self.config["Timeout"].getint("Generic")
            self.successful = True
        except Exception as e:
            self.successful = False
            print("Error parsing config.")
            print(e)