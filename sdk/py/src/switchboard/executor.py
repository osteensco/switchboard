from switchboard.enums import Cloud
from switchboard.invocation import Invoke
from switchboard.cloud import (
        AWS_find_executor_endpoint, 
        AZURE_find_executor_endpoint, 
        GCP_find_executor_endpoint
)



# The switchboard executor function will be wrapped in a simple serverless function call as demonstrated below.
#
#   def lambda_handler(event, context):
#       return switchboard_executor(context)
#
#   



def discover_executor_endpoint(cloud: Cloud, name: str) -> str:
    match cloud:
        case Cloud.AWS:
            return AWS_find_executor_endpoint(name)
        case Cloud.GCP:
            return GCP_find_executor_endpoint(name)
        case Cloud.AZURE:
            return AZURE_find_executor_endpoint(name)
        case Cloud.CUSTOM:
            return ""
        case _:
            raise UnsupportedCloud(f"Cannot discover endpoint of invocation queue for unsupported cloud: {cloud}")
    return ""



def push_to_executor(cloud: Cloud, name: str, body: str) -> dict:

    ep = discover_executor_endpoint(cloud, name)

    response = Invoke(cloud, ep, body)
    return response



def switchboard_execute(context):
    pass



