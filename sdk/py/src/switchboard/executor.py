from .db import DBInterface
from .enums import Cloud, SwitchboardComponent
from .invocation import Invoke
from .schemas import Task




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
#   from tasks import directory_map #tasks.py in lambda directory
#
#   def lambda_handler(event, context):
#       try:
#           status = switchboard_execute(context, directory_map)
#       except Exception as e:
#           status = 400
#       finally:
#           return status

def switchboard_execute(context, directory_map):
# Potential task categories that the executor should handle
#   [ ] http endpoint
#   [ ] compute (via sdk)
#   [ ] job (via sdk)
#   [ ] message queue
#   [ ] storage/DB operation (via sdk)
#   [ ] ML/Data Pipeline (via sdk)
#   [ ] Event emitter/bus
# For initial support, focus on http, message cloud native message queues, and event emission


# Alt approach
#   executor looks for tasks.py
#   task.py should contain Task (Operator in airflow) objects with an execute parameter
#   dictionary called 'directory_map'
#       this is just dictionary of tasks
#   context provides key to use for function call
#   this allows for user to execute literally anything they want

# TODO
#   work backwords in the flow to ensure the 'execute' key is part of the context for each step
    task = directory_map[context['execute']]
    return task.execute() # all functions passed into tasks inside of the directory_map should return a valid status code



