from typing import final
import pytest
import json
from unittest.mock import MagicMock, patch

from switchboard.enums import Cloud, Status
from switchboard.workflow import ClearWorkflow, InitWorkflow, Call, Done
from switchboard.db import DB, DBInterface
from switchboard.schemas import State, Context
from switchboard.executor import switchboard_execute
from .tasks import directory_map


class DBMockInterface(DBInterface):
    def __init__(self, state: State | None) -> None:
        self.all_states, self.id_max = self._prepopulate(state)

    def _prepopulate(self, state: State | None) -> tuple[dict, int]:
        if state:
            return {state.run_id: state}, state.run_id
        return {}, 0

    def read(self, name, id):
        try:
            state = self.all_states[id]
            return state
        except KeyError:
            return None

    def write(self, state):
        self.all_states[state.run_id] = state

    def get_endpoint(self, name, component):
        return "mocked/endpoint"

    def increment_id(self, name):
        self.id_max += 1
        return self.id_max

    def get_table(self, table):
        pass


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
    assert status == 200, "!!!!!"
