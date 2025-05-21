from enum import Enum





class Cloud(Enum):
    AWS = 'AWS'
    GCP = 'GCP'
    AZURE = 'AZURE'
    CUSTOM = 'CUSTOM'



class CloudResource(Enum):
    # AWS
    SQS = 'SQS'
    DYNAMODB = 'DYNAMODB'
    LAMBDA = 'LAMBDA'
    EVENTBRIDGE = 'EVENTBRIDGE'
    SCHEDULER = 'SCHEDULER' # event bridge scheduler (cron job)

    #GCP

    #AZURE



class CloudResourceType(Enum):
    QUEUE = "QUEUE"
    DATASTORE = "DATASTORE"
    COMPUTE = "COMPUTE"
    EVENT_EMITTER = "EVENT_EMITTER"
    CRON = "CRON"



class Status(Enum):
    InProcess = 'InProcess'
    Completed = 'Completed'
    OutOfRetries = 'OutOfRetries'



class TableName(Enum):
    SwitchboardState = 'SwitchboardState'
    # table for discoverable resources. see schemas.Endpoint.
    SwitchboardResources = 'SwitchboardResources'



class SwitchboardComponent(Enum):
    InvocationQueue = 'InvocationQueue'
    ExecutorQueue = 'ExecutorQueue'


