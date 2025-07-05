from typing import final
import pytest
import json
from unittest.mock import MagicMock, patch

from switchboard.enums import Cloud, Status
from switchboard.response import Response
from switchboard.workflow import ClearWorkflow, InitWorkflow, Call, Done
from switchboard.db import DB, DBInterface
from switchboard.schemas import State, Context
from switchboard.executor import switchboard_execute
from .tasks import directory_map
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

    context = '{"ids": [-1,-1,-1], "executed": true, "completed": true, "success": true}'

    def workflow_serverless_function(context):
        db = DB(Cloud.CUSTOM, DBMockInterface(None))
        InitWorkflow(Cloud.CUSTOM, 'test_workflow', db, context)
    
        Call("my_task")

        Call("my_other_task")

        Call("final_task")

        Done()

        # ensure the workflow object is cleared to mimic a serverless function's end of life
        ClearWorkflow()

    def executor_serverless_function(context):
        status = 500
        try:
            status = switchboard_execute(context, directory_map)
        except BaseException as e: 
            print(e)
        finally:
            return status





