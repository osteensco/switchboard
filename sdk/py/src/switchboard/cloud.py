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
def AWS_message_push(msg: str):
    pass

def GCP_message_push(msg: str):
    pass

def AZURE_message_push(msg: str):
    pass







# Eexceptions
class UnsupportedCloud(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"UnsupportedCloud Error: {self.message}"




