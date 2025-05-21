import json
from switchboard.db import DBInterface
from switchboard.enums import Cloud, SwitchboardComponent
from switchboard.invocation import Invoke
from switchboard.cloud import (
        AWS_find_executor_endpoint, 
        AZURE_find_executor_endpoint, 
        GCP_find_executor_endpoint,
        UnsupportedCloud
)



# TODO 
#   Determine how to handle pubsub pattern
#   ParallelStep does this already in a way, but consider the use case below 
#       https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/pub-sub.html
#       Replacing these implementations with switchboard would require additional SQS or SNS queue(s) from the executor -> microservice
#           This migration requirement is in conflict with the goals of this framework
#           Should switchboard provide batteries included queues + compute scaffolding to alleviate this sort of thing? Is it even a real problem?



def discover_executor_endpoint(cloud: Cloud, name: str) -> str:
    match cloud:
        case Cloud.AWS:
            return AWS_find_executor_endpoint(name)
        case Cloud.GCP:
            return GCP_find_executor_endpoint(name)
        case Cloud.AZURE:
            return AZURE_find_executor_endpoint(name)
        case _:
            raise UnsupportedCloud(f"Cannot discover endpoint of invocation queue for unsupported cloud: {cloud}")




def push_to_executor(cloud: Cloud, db: DBInterface, name: str, body: str, pubsub: bool=False) -> dict:

    ep = db.get_endpoint(name, SwitchboardComponent.ExecutorQueue)
    if pubsub:
        pubsub_body = json.loads(body)
        pubsub_body['pubsub'] = True
        body = json.dumps(pubsub_body)

    response = Invoke(cloud, ep, body)
    return response



# The switchboard executor function will be wrapped in a simple serverless function call as demonstrated below.
#
#   def lambda_handler(event, context):
#       try:
#           status = switchboard_execute(context)
#       except Exception as e:
#           status = 400
#       finally:
#           return status

def switchboard_execute(context):
    # look up endpoint in database and push context to it
    # if context['pubsub']:
    #     collect all parallel steps
    #     once collected push to pubsub queue

    pass



