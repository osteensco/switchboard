from typing import Callable

from switchboard.response import Response
from .db import DBInterface
from .enums import Cloud, SwitchboardComponent
from .invocation import QueuePush
from .schemas import Context, Task
from .logging_config import log









def push_to_executor(cloud: Cloud, db: DBInterface, name: str, body: str, custom_execution_queue: Callable | None = None) -> dict:

    ep = db.get_endpoint(name, SwitchboardComponent.ExecutorQueue)
    print(f"!!!!!! Executor endpoint: '{ep}'")

    response = QueuePush(cloud, ep, body, custom_execution_queue)
    return response



# The switchboard executor function will be wrapped in a simple serverless function call.
# It is important to note that the executor function will vary based on the cloud provider used.
# See examples directory for specific examples.
def switchboard_execute(
        cloud: Cloud, 
        db: DBInterface,
        context: dict,
        task_map: dict[str, Task],
        custom_invocation_queue: Callable | None = None
) -> int:
    '''
    Switchboard's execution function for use by the executor.

    generic support
      switchboard provides out of the box support for any job or worker a user wants switchboard to orchestrate
      the method of triggering the user's business logic will need to be defined by the user
      
    process:
      - executor looks for tasks.py
      - tasks.py should contain a dictionary called 'task_map' and mapped functions that contain light business logic or logic that triggers another service containing business logic
      - the 'task_map' should contain key value pairs with each value being a Task object (a Task is like an Operator in airflow)
      - context provides key to use for function call (this is the 'task_key' field)

    pubsub pattern support:
        For reference: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/pub-sub.html
          - User defines a task that publishes a message to the pubsub queue and each worker would need to have a Response() object created as part of their code

    The context passed to the executor will have one additonal field -
      'task_key': the task that should be executed, this correspond to a key in `task_map` - str
    '''

    if (task_key := context['task_key']) in task_map:
        log.bind(
            component="executor_service",
            workflow_name=context.get('workflow'),
            run_id=context.get('ids', [None])[0],
            context=context,
            task_key=task_key
        ).info("-- Executor attempting to call task from task_map. --")
        # once we grab the task_key we remove it from the context so we can more easily create the Context object
        task = task_map[task_key]
        del context["task_key"]

        # all functions passed into tasks inside of the task_map should take 
        # the raw context as an argument and return a valid status code
        cntxt = Context(**context)
        cntxt.executed = True

        executor_response = Response(cloud, db, context['workflow'], cntxt, custom_queue_push=custom_invocation_queue)
        executor_response.send()
        
        # tasks take a Context object as an argument
        task_response = task.execute(cntxt)
        return task_response
    else:
        return 404



