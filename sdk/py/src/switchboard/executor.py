import json
from switchboard.db import DBInterface
from switchboard.enums import Cloud, SwitchboardComponent
from switchboard.invocation import Invoke
from switchboard.cloud import (
        UnsupportedCloud
)



# TODO 
#   Determine how to handle pubsub pattern
#   ParallelStep does this already in a way, but consider the use case below 
#       https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/pub-sub.html
#       Replacing these implementations with switchboard would require additional SQS or SNS queue(s) from the executor -> microservice
#           This migration requirement is in conflict with the goals of this framework
#           Should switchboard provide batteries included queues + compute scaffolding to alleviate this sort of thing? Is it even a real problem?





def push_to_executor(cloud: Cloud, db: DBInterface, name: str, body: str) -> dict:

    ep = db.get_endpoint(name, SwitchboardComponent.ExecutorQueue)

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
# Potential task categories that the executor should handle
#   [ ] http endpoint
#   [ ] compute (via sdk)
#   [ ] job (via sdk)
#   [ ] message queue
#   [ ] storage/DB operation (via sdk)
#   [ ] ML/Data Pipeline (via sdk)
# For initial support, focus on http and message cloud native message queues




    pass



