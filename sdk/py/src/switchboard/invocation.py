from typing import Callable

from .db import DBInterface
from .cloud import (
    AWS_message_push,
    GCP_message_push, 
    AZURE_message_push
)
from .enums import Cloud, SwitchboardComponent



def QueuePush(cloud: Cloud, endpoint: str, body: str, custom_queue_push: Callable | None = None) -> dict:
    '''
    Interface for interacting with the switchboard invocation and execution queues.
    '''
    match cloud:
        case Cloud.AWS:
            return AWS_message_push(endpoint, body)
        case Cloud.GCP:
            return GCP_message_push(body)
        case Cloud.AZURE:
            return AZURE_message_push(body)
        case Cloud.CUSTOM:
            assert custom_queue_push is not None, "Custom queue indicated but no queue push function provided!"
            return custom_queue_push(body)



def discover_invocation_endpoint(db: DBInterface, name: str) -> str:
    '''
    Queries the SwitchboardResources table for the desired queue endpoint url.
    '''
    return db.get_endpoint(name, SwitchboardComponent.InvocationQueue)



