from enum import Enum





class Cloud(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'
    CUSTOM = 'CUSTOM'


class Status(Enum):
    InProcess = 'InProcess'
    Completed = 'Completed'
    OutOfRetries = 'OutOfRetries'

class TableName(Enum):
    Dynamodb = 'dynamodb'



