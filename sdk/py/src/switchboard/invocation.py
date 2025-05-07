from .cloud import AWS_message_push, GCP_message_push, AZURE_message_push, UnsupportedCloud
from .enums import Cloud



# Interface for interacting with the switchboard invocation queue
def Invoke(cloud: Cloud, body: str):
    def __init__(self, cloud: Cloud, body: str) -> None:
        match cloud:
            case Cloud.AWS:
                AWS_message_push(body)
            case Cloud.GCP:
                GCP_message_push(body)
            case Cloud.AZURE:
                AZURE_message_push(body)
            case _:
                raise UnsupportedCloud
        return






