from enum import Enum





class Cloud(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'


class Status(Enum):
    InProcess = 'InProcess'
    Completed = 'Completed'
    OutOfRetries = 'OutOfRetries'


class Queue(Enum):
    INVOCATION = "INVOCATION"
    EXECUTOR = "EXECUTOR"



