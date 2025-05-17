import boto3




# Database connectors
def AWS_db_connect():
    '''
    requires the following env vars:
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_DEFAULT_REGION=your_region

    Returns a dynamodb service resource - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#guide-resources

    '''
    return boto3.resource('dynamodb')


def GCP_db_connect():
    pass

def AZURE_db_connect():
    pass


# Message queue publishers
def AWS_message_push(endpoint: str, msg: str) -> dict:
    sqs = boto3.client("sqs")
    try:
        response = sqs.send_message(
            QueueUrl=endpoint,
            MessageBody=msg
        )
        return response
    except Exception as e:
        raise e

def GCP_message_push(msg: str) -> dict:
    return {}

def AZURE_message_push(msg: str) -> dict:
    return {}


# Invocation queue endpoint discovery
def AWS_find_invocation_endpoint(name: str) -> str:
    #TODO 
    #   implement me
    return ""

def GCP_find_invocation_endpoint(name: str) -> str:
    return ""

def AZURE_find_invocation_endpoint(name: str) -> str:
    return ""


# Executor queue endpoint discovery
def AWS_find_executor_endpoint(name: str) -> str:
    #TODO 
    #   implement me
    return ""

def GCP_find_executor_endpoint(name: str) -> str:
    return ""

def AZURE_find_executor_endpoint(name: str) -> str:
    return ""


# Eexceptions
class UnsupportedCloud(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"UnsupportedCloud Error: {self.message}"




