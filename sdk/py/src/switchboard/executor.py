from .db import DBInterface
from .enums import Cloud, SwitchboardComponent
from .invocation import Invoke
from .schemas import Task









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



# generic support
#   switchboard provides out of the box support for any job or worker a user wants switchboard to orchestrate
#   the trigger of the user's business logic will need to be defined by the user
#   while slightly cumbersome, this provides control and flexibility for the user
#   
# process:
#   executor looks for tasks.py
#   tasks.py should contain Task (Operator in airflow) objects with an execute parameter
#   dictionary called 'directory_map'
#       this is just dictionary of tasks
#   context provides key to use for function call
#   this allows for user to execute literally anything they want

# pubsub pattern support:
#       https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/pub-sub.html
#       user defines a task that publishes a message to the pubsub queue and each worker would need to have a Response() object created as part of their code
    
    if (task_key := context['execute']) in directory_map:
        task = directory_map[task_key]
        return task.execute() # all functions passed into tasks inside of the directory_map should return a valid status code
    else:
        return 404



