from typing import Callable
from .cloud import AWS_message_push, GCP_message_push, AZURE_message_push, UnsupportedCloud
from .enums import Cloud



# Interface for interacting with the switchboard invocation queue
def Invoke(cloud: Cloud, body: str, custom_queue_push: Callable | None = None):
    match cloud:
        case Cloud.AWS:
            AWS_message_push(body)
        case Cloud.GCP:
            GCP_message_push(body)
        case Cloud.AZURE:
            AZURE_message_push(body)
        case Cloud.CUSTOM:
            assert custom_queue_push is not None
            custom_queue_push(body)
        case _:
            raise UnsupportedCloud(f"Cannot push message to invocation queue of unsupported cloud: {cloud}")
    return






