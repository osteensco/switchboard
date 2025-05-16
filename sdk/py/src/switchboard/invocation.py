from typing import Callable
from .cloud import AWS_message_push, GCP_message_push, AZURE_message_push, UnsupportedCloud
from .enums import Cloud



# Interface for interacting with the switchboard invocation queue
def Invoke(cloud: Cloud, endpoint: str, body: str, custom_queue_push: Callable | None = None):
    match cloud:
        case Cloud.AWS:
            return AWS_message_push(endpoint, body)
        case Cloud.GCP:
            return GCP_message_push(body)
        case Cloud.AZURE:
            return AZURE_message_push(body)
        case Cloud.CUSTOM:
            assert custom_queue_push is not None
            return custom_queue_push(body)
        case _:
            raise UnsupportedCloud(f"Cannot push message to invocation queue of unsupported cloud: {cloud}")
    return






