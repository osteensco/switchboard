from typing import Callable
from .db import DBInterface
from .enums import Cloud, SwitchboardComponent
from .invocation import Invoke
from .schemas import Context, Task









def push_to_executor(cloud: Cloud, db: DBInterface, name: str, body: str, custom_execution_queue: Callable | None = None) -> dict:

    ep = db.get_endpoint(name, SwitchboardComponent.ExecutorQueue)

    response = Invoke(cloud, ep, body, custom_execution_queue)
    return response



# The switchboard executor function will be wrapped in a simple serverless function call as demonstrated below.
# It is important to note that the executor function will vary based on the cloud provider used.
#
#   import json
#   from .tasks import directory_map #tasks.py in lambda directory
#
#   def lambda_handler(event, context):
#       assert len(event['Records']) == 1, f"Event records array does not equal 1, ensure the executor's queue batch size is set to 1. event['Records']: {event['Records']}"
#       sb_context = json.loads(event['Records'][0]['body'])
#       try:
#           status = switchboard_execute(sb_context, directory_map)
#       except Exception as e:
#           status = 400
#       finally:
#           return status

def switchboard_execute(context: dict, directory_map: dict[str, Task]) -> int:
# Potential task categories that the executor should handle
#   [ ] http endpoint
#   [ ] compute (via sdk)
#   [ ] job (via sdk)
#   [ ] message queue
#   [ ] storage/DB operation (via sdk)
#   [ ] ML/Data Pipeline (via sdk)
#   [ ] Event emitter/bus



# generic support
#   switchboard provides out of the box support for any job or worker a user wants switchboard to orchestrate
#   the trigger of the user's business logic will need to be defined by the user
#   while slightly cumbersome, this provides control and flexibility for the user
#   
# process:
#   - executor looks for tasks.py
#   - tasks.py should just contain a dictionary called 'directory_map' 
#   - the 'directory_map' should contain key value pairs with each value being a Task object (a Task is like an Operator in airflow)
#   - context provides key to use for function call (this is the 'execute' field)
#   - this allows for users to trigger anything they'd like through any means they like

# pubsub pattern support:
#       https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/pub-sub.html
#       user defines a task that publishes a message to the pubsub queue and each worker would need to have a Response() object created as part of their code
    
    if (task_key := context['execute']) in directory_map:
        task = directory_map[task_key]

        # all functions passed into tasks inside of the directory_map should take 
        # the raw context as an argument and return a valid status code

        return task.execute(Context(context["ids"],context["executed"],context["completed"],context["success"],context["cache"]))
    else:
        return 404



