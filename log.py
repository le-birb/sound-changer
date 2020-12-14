
from os import path

class logger:

    def __init__(self, dir = path.dirname(__file__), file = "soundchanger_log"):
        self.log_file = open(path.join(dir, file), "w")

    def log(self, message: str):
        self.log_file.write(message + "\n")
        self.log_file.flush()
    
    def log_warning(self, message):
        prefix = "[Warning]: "
        self.log_file.write(prefix + message + "\n")
        self.log_file.flush()

    def log_error(self, message):
        prefix = "[Error]: "
        self.log_file.write(prefix + message + "\n")
        self.log_file.flush()
