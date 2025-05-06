from .cloud import AWS_message_push, GCP_message_push, AZURE_message_push
from .enums import Cloud



# Interface for interacting with the switchboard invocation queue
class Invoke():
    def __init__(self, cloud: Cloud, body: str) -> None:
        self.publish_to_queue(cloud, body)
       
    @staticmethod
    def publish_to_queue(cloud, body):
        match cloud:
            case Cloud.AWS:
                AWS_message_push(body)
            case Cloud.GCP:
                GCP_message_push(body)
            case Cloud.AZURE:
                AZURE_message_push(body)
            case _:
                raise ValueError
        return






