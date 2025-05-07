




# Database connectors
def AWS_db_connect():
    pass

def GCP_db_connect():
    pass

def AZURE_db_connect():
    pass


# Message queue publishers
def AWS_message_push(msg: str):
    pass

def GCP_message_push(msg: str):
    pass

def AZURE_message_push(msg: str):
    pass


# Database Interfaces
class AWS_DataInterface:
    @staticmethod
    def read(id):
        pass

    @staticmethod
    def write(id,state):
        pass

    @staticmethod
    def increment_id(id):
        pass


class GCP_DataInterface:
    @staticmethod
    def read(id):
        pass

    @staticmethod
    def write(id,state):
        pass

    @staticmethod
    def increment_id(id):
        pass


class AZURE_DataInterface:
    @staticmethod
    def read(id):
        pass

    @staticmethod
    def write(id,state):
        pass

    @staticmethod
    def increment_id(id):
        pass






class UnsupportedCloud(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"UnsupportedCloud Error: {self.message}"




