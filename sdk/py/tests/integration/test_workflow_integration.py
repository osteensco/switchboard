from typing import final
import pytest
import json
from unittest.mock import MagicMock, patch

from switchboard.enums import Cloud, Status
from switchboard.response import Response, Trigger
from switchboard.workflow import ClearWorkflow, InitWorkflow, Call, Done, SetCustomExecutorQueue
from switchboard.db import DB, DBInterface
from switchboard.schemas import State, Context
from switchboard.executor import switchboard_execute
from .tasks import directory_map, mock_invocation_queue
from .db import DBMockInterface



@pytest.mark.integration
def test_workflow_integration():
    # 1. Initialize the workflow
    db = DB(Cloud.CUSTOM, DBMockInterface(None))
    context = '{"ids": [-1,-1,-1], "executed": true, "completed": true, "success": true}'
    InitWorkflow(Cloud.CUSTOM, 'test_workflow', db, context)

    # 2. Mock the executor push
    with patch('switchboard.workflow.push_to_executor') as mock_push_to_executor:
        # 3. Call the first task
        Call("my_task")

        # 4. Assert that the executor was called
        mock_push_to_executor.assert_called_once()
        args, kwargs = mock_push_to_executor.call_args
        assert args[0] == Cloud.CUSTOM
        assert args[1] == db.interface
        assert args[2] == 'test_workflow'
        assert json.loads(args[3]) == {"execute": "my_task"}

        # 5. Simulate the executor
        executor_context = json.loads(args[3])
        status = switchboard_execute(executor_context, directory_map)
        assert status == 200

        final_status = Done()
        assert final_status == 200

    # 6. Simulate the response from the executor
    ClearWorkflow()
    response_context = '{"ids": [1, 1, -1], "executed": true, "completed": true, "success": true}'
    InitWorkflow(Cloud.CUSTOM, 'test_workflow', db, response_context)

    Call("my_task")

    status = Done()
    assert status == 200



@pytest.mark.integration
def test_endtoend_integration():
    db = DB(Cloud.CUSTOM, DBMockInterface(None))
    
    # Simulate two distinct message queues for the two microservices
    workflow_queue = []
    executor_queue = []

    # Define custom push functions for the services
    def push_to_workflow_queue(body):
        workflow_queue.append(body)

    def push_to_executor_queue(body):
        executor_queue.append(body)

    def workflow_serverless_function(context):
        # The workflow service uses a custom push function to send messages to the executor
        InitWorkflow(Cloud.CUSTOM, 'test_workflow', db, context)
        SetCustomExecutorQueue(push_to_executor_queue)
    
        Call("my_task")
        Call("my_other_task")
        Call("final_task")

        Done()
        ClearWorkflow()

    def executor_serverless_function(context):
        # The executor service gets its custom push function via the response object in tasks.py
        # We need to ensure tasks.py is configured to push back to the workflow_queue
        mock_invocation_queue.set_push_function(push_to_workflow_queue)

        cntxt = json.loads(context)
        switchboard_execute(cntxt, directory_map)


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
    assert len(final_state.steps) == 3, f"{final_state.steps}"
    assert final_state.steps[0].step_id == 1
    assert final_state.steps[1].step_id == 2
    assert final_state.steps[2].step_id == 3
    assert final_state.steps[2].success



