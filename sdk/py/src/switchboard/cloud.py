import boto3

from switchboard.logging_config import log




# Database connectors
def AWS_db_connect():
    '''
    requires the following env vars:
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_DEFAULT_REGION=your_region

    Returns a dynamodb service resource - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#guide-resources

    '''
    # TODO remove hardcoded region_name
    # return boto3.resource('dynamodb', region_name='us-east-1')
    return boto3.resource('dynamodb')


def GCP_db_connect():
    pass

def AZURE_db_connect():
    pass


# Message queue publishers
def AWS_message_push(endpoint: str, msg: str) -> dict:
    sqs = boto3.client("sqs")
    response = {}
    try:
        response = sqs.send_message(
            QueueUrl=endpoint,
            MessageBody=msg
        )
    except Exception as e:
        log.bind(
            component="db_service",
            endpoint=endpoint,
            msg=msg
        ).error(e)
        raise 
    finally:
        return response

def GCP_message_push(msg: str) -> dict:
    return {}

def AZURE_message_push(msg: str) -> dict:
    return {}





# Exceptions
class UnsupportedCloud(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"UnsupportedCloud Error: {self.message}"




