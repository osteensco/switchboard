import pytest
import json

from switchboard.enums import Cloud
from switchboard.response import Trigger
from switchboard.workflow import GetCache, InitWorkflow, Call, Done, ParallelCall, SetCustomExecutorQueue, Workflow
from switchboard.db import DB
from switchboard.executor import switchboard_execute
from .tasks import task_map, mock_invocation_queue
from .db import DBMockInterface







@pytest.mark.integration
def test_endtoend_integration():
    db = DB(Cloud.CUSTOM, DBMockInterface(None))
    
    # Simulate message queues
    workflow_queue = []
    executor_queue = []

    # Define custom push functions for the services
    # For testing we have to utilize Cloud.CUSTOM
    def push_to_workflow_queue(body):
        print(f"body pushed to workflow queue: {body}")
        workflow_queue.append(body)

    def push_to_executor_queue(body):
        print(f"body pushed to executor queue: {body}")
        executor_queue.append(body)

    def workflow_serverless_function(context):
        InitWorkflow(Cloud.CUSTOM, 'test_workflow', db, context)
        # The workflow service uses a custom push function to send messages to the executor
        SetCustomExecutorQueue(push_to_executor_queue)
        
        # Initialize workflow's cache
        cache = {"test_true": None, "test_false": None} | GetCache()

        Call("step1", "my_task")
        Call("step2", "my_other_task")
        Call("step3", "final_task")

        ParallelCall("step4", ("psyyych",0), ("anotherone",0), ("yetanother",0))
        if cache["test_true"]:
            ParallelCall("step5", ("conditional1", 0), ("conditional2",0))
        else:
            print(f"!!!!! - 'test_true'={cache["test_true"]}")
            Call("badstep1", "ishouldntrun1")
        if cache["test_false"]:
            print(f"!!!!! - 'test_false'={cache["test_false"]}")
            Call("badstep2", "ishouldntrun2")

        Call("endstep", "endstep")

        Done()
        Workflow._reset_singleton()
        
    def executor_serverless_function(context):
        # The executor service gets its custom push function via the response object in tasks.py
        # We need to ensure tasks.py is configured to push back to the workflow_queue
        mock_invocation_queue.set_push_function(push_to_workflow_queue)

        cntxt = json.loads(context)
        switchboard_execute(Cloud.CUSTOM, db.interface, cntxt, task_map, custom_invocation_queue=push_to_workflow_queue)


    # 1. Trigger the start of the workflow
    # The trigger sends the initial message to the workflow_queue
    Trigger(Cloud.CUSTOM, db.interface, "my_workflow", custom_queue_push=push_to_workflow_queue)
    assert len(workflow_queue) == 1
    assert len(executor_queue) == 0

    # 2. Process messages in a loop to simulate parallel execution
    while workflow_queue or executor_queue:
        # Process one message from the workflow queue
        if workflow_queue:
            workflow_payload = workflow_queue.pop(0)
            workflow_serverless_function(workflow_payload)

        # Process one message from the executor queue
        if executor_queue:
            executor_payload = executor_queue.pop(0)
            executor_serverless_function(executor_payload)


    # 3. Assert the final state
    final_state = db.interface.read('test_workflow', 1)
    assert final_state is not None
    assert len(final_state.steps) == 6, f"{final_state.steps}"
    assert [step.step_id for step in final_state.steps] == [0,1,2,3,4,5]
    assert [step.step_name for step in final_state.steps] == ['step1', 'step2', 'step3', 'step4', 'step5', 'endstep']
    assert [step.success for step in final_state.steps] == [True,True,True,True,True,True]
    assert final_state.cache == {"test_true": True, "test_false": False}



