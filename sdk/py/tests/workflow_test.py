import pytest
import json
from unittest.mock import patch, MagicMock
from switchboard.enums import Cloud
from switchboard.schemas import State, Context, Step, ParallelStep
import switchboard.workflow as wf
from switchboard.db import DB, DBInterface


# A default, valid context for initializing a new workflow.
NEW_WORKFLOW_CONTEXT = json.dumps({
    "ids": [-1, -1, -1],
    "executed": False,
    "completed": False,
    "success": False,
    "cache": {}
})


@pytest.fixture
def mock_db():
    """Fixture to create a mock DBInterface."""
    db_mock = MagicMock(spec=DBInterface)
    return DB(Cloud.CUSTOM, db_mock), db_mock


@pytest.fixture(autouse=True, scope="function")
def clear_singleton():
    print("!!!!!!! - clear WORKFLOW singleton")
    # if wf.WORKFLOW:
    #     wf.Workflow._instance = None
    #     wf.Workflow._initialized = False
    wf.WORKFLOW = None



def test_InitWorkflow_for_new_run(mock_db):
    """
    InitWorkflow should correctly initialize a new state.
    """

    db, db_mock = mock_db
    db_mock.read.return_value = None
    db_mock.increment_id.return_value = 123

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_workflow", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    assert wf.WORKFLOW is not None
    assert wf.WORKFLOW.state.name == "test_workflow"
    assert wf.WORKFLOW.state.run_id == 123
    db_mock.read.assert_called_once_with("test_workflow", -1)
    db_mock.increment_id.assert_called_once_with("test_workflow")



def test_InitWorkflow_for_existing_run(mock_db):
    """
    InitWorkflow should correctly load and update an existing state.
    """
    assert wf.WORKFLOW is None
    db, db_mock = mock_db
    existing_state = State(
        name="test_workflow",
        run_id=456,
        steps=[Step(step_id=0, step_name="step1", task_key="task1")],
        cache={"initial_data": "value"},
    )
    db_mock.read.return_value = existing_state
    
    context_json = json.dumps({
        "ids": [456, 0, -1],
        "executed": True,
        "completed": False,
        "success": False,
        "cache": {"new_data": "added"}
    })

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_workflow", db=db, context=context_json)
    
    assert wf.WORKFLOW is not None
    db_mock.read.assert_called_once_with("test_workflow", 456)
    assert wf.WORKFLOW.state.steps[0].executed is True
    assert wf.WORKFLOW.state.steps[0].completed is False
    assert wf.WORKFLOW.state.cache == {"initial_data": "value", "new_data": "added"}


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_Call_enqueues_task_for_new_step(mock_enqueue, mock_db):
    """
    Call should call _enqueue_execution when a step is called for the first time.
    """
    db, _ = mock_db

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.Call("first_step", "do_work")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus)
    assert len(wf.WORKFLOW.state.steps) == 1
    assert wf.WORKFLOW.state.steps[0].step_name == "first_step"
    mock_enqueue.assert_called_once()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_Call_is_noop_if_step_already_completed(mock_enqueue, mock_db):
    """
    Call should not call _enqueue_execution when step was already completed.
    """
    db, _ = mock_db

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    assert(isinstance(wf.WORKFLOW,wf.Workflow))
    wf.WORKFLOW.state.steps.append(Step(step_id=0, step_name="first_step", executed=True, completed=True, success=True, task_key="do_work"))
    wf.WORKFLOW.step_cnt = 1

    wf.Call("first_step", "do_work")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus) 
    mock_enqueue.assert_not_called()

# TODO
#   - test other outcomes of the call method



@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_ParallelCall_enqueues_multiple_tasks(mock_enqueue, mock_db):
    """
    ParallelCall should call _enqueue_execution for each task passed to it.
    """
    assert wf.WORKFLOW is None
    db, _ = mock_db
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.ParallelCall("parallel_step", "task_a", "task_b")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus)
    assert isinstance(wf.WORKFLOW.state.steps[0], ParallelStep)
    assert mock_enqueue.call_count == 2

# TODO
#   - test other outcomes of the parallel_call method

def test_GetCache_returns_current_state_cache(mock_db):
    db, _ = mock_db
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    assert(isinstance(wf.WORKFLOW, wf.Workflow))
    wf.WORKFLOW.state.cache = {"test_key": "test_value"}
    
    assert wf.GetCache() == {"test_key": "test_value"}


def test_Done_returns_200(mock_db):
    db, _ = mock_db
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    assert wf.Done() == 200


# def test_ClearWorkflow_resets_the_singleton(mock_db):
#     db, _ = mock_db
#    
#     wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
#    
#     assert wf.WORKFLOW is not None
#     wf.ClearWorkflow(Cloud.CUSTOM, "test_wf", db, NEW_WORKFLOW_CONTEXT)
#     assert wf.WORKFLOW is None




