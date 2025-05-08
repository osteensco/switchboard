from abc import ABC, abstractmethod





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


# Database Interface
class DBInterface(ABC):
    @abstractmethod
    def read(self,id):
        pass

    @abstractmethod
    def write(self,id,state):
        pass

    @abstractmethod
    def increment_id(self,id):
        pass


class AWS_DataInterface(DBInterface):
    def read(self,id):
        pass

    def write(self,id,state):
        pass

    def increment_id(self,id):
        pass


class GCP_DataInterface(DBInterface):
    def read(self,id):
        pass

    def write(self,id,state):
        pass

    def increment_id(self,id):
        pass


class AZURE_DataInterface(DBInterface):
    def read(self,id):
        pass

    def write(self,id,state):
        pass

    def increment_id(self,id):
        pass





# Eexceptions
class UnsupportedCloud(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"UnsupportedCloud Error: {self.message}"




