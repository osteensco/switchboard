import pytest
import json
from unittest.mock import patch, MagicMock
from switchboard.enums import Cloud
from switchboard.schemas import State, Context, Step, ParallelStep
from switchboard.db import DB, DBInterface
import switchboard.workflow as wf


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
    yield
    # After the test runs, reset the singleton state
    wf.Workflow._reset_singleton()
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

    db, db_mock = mock_db
    existing_state = State(
        name="test_workflow",
        run_id=456,
        steps=[Step(step_id=0, step_name="step1", task_key="task1", retries=0)],
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
    assert wf.WORKFLOW.state.steps[0].executed is True, f"{wf.WORKFLOW}"
    assert wf.WORKFLOW.state.steps[0].completed is False
    assert wf.WORKFLOW.state.cache == {"initial_data": "value", "new_data": "added"}


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_Call_enqueues_task_for_new_step(mock_enqueue, mock_db):
    """
    Call should call _enqueue_execution when a step is called for the first time.
    """

    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.Call("first_step", "do_some_work")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus)
    assert len(wf.WORKFLOW.state.steps) == 1
    assert wf.WORKFLOW.state.steps[0].step_name == "first_step"
    mock_enqueue.assert_called_once()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_Call_is_noop_if_step_already_completed(mock_enqueue, mock_db):
    """
    Call should not call _enqueue_execution when step was already completed.
    """
    
    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    assert(isinstance(wf.WORKFLOW,wf.Workflow))
    wf.WORKFLOW.state.steps.append(Step(step_id=0, step_name="first_step", executed=True, completed=True, success=True, task_key="do_work", retries=0))
    wf.WORKFLOW.step_cnt = 1

    wf.Call("first_step", "do_work")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus) 
    mock_enqueue.assert_not_called()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_Call_respects_WaitStatus(mock_enqueue, mock_db):
    """
    Call should not enqueue a task if the workflow is already in a WaitStatus.
    """
    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    # Manually set the workflow to a waiting state
    wf.WORKFLOW = wf.WaitStatus(status=wf.Status.InProcess, state=wf.WORKFLOW.state)

    wf.Call("second_step", "do_another_thing")

    mock_enqueue.assert_not_called()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_ParallelCall_enqueues_multiple_tasks(mock_enqueue, mock_db):
    """
    ParallelCall should call _enqueue_execution for each task passed to it.
    """

    db, db_mock = mock_db
    db_mock.read.return_value = None
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.ParallelCall("parallel_step", "task_a", "task_b")
    
    assert isinstance(wf.WORKFLOW, wf.WaitStatus)
    assert isinstance(wf.WORKFLOW.state.steps[0], ParallelStep)
    assert mock_enqueue.call_count == 2


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_ParallelCall_respects_WaitStatus(mock_enqueue, mock_db):
    """
    ParallelCall should not enqueue tasks if the workflow is already in a WaitStatus.
    """
    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    # Manually set the workflow to a waiting state
    wf.WORKFLOW = wf.WaitStatus(status=wf.Status.InProcess, state=wf.WORKFLOW.state)

    wf.ParallelCall("parallel_step", "task_a", "task_b")

    mock_enqueue.assert_not_called()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_conditional_logic_in_workflow(mock_enqueue, mock_db):
    """
    Workflow should correctly execute conditional steps based on cache values.
    """
    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.WORKFLOW.state.cache["should_run"] = True

    if wf.GetCache().get("should_run"):
        wf.Call("conditional_step", "do_something_conditionally")
    
    mock_enqueue.assert_called_once()

    # Reset and test the negative case
    wf.Workflow._reset_singleton()
    wf.WORKFLOW = None
    mock_enqueue.reset_mock()

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    wf.WORKFLOW.state.cache["should_run"] = False

    if wf.GetCache().get("should_run"):
        wf.Call("conditional_step", "do_something_conditionally")
    
    mock_enqueue.assert_not_called()


def test_workflow_with_no_steps(mock_db):
    """
    A workflow with no calls should complete successfully.
    """
    db, db_mock = mock_db
    db_mock.read.return_value = None

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    result = wf.Done()

    assert result == 200
    assert wf.WORKFLOW.status == wf.Status.Completed


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_SetCustomExecutorQueue_is_called(mock_enqueue, mock_db):
    """
    The custom executor queue function should be called when provided.
    """
    db, db_mock = mock_db
    db_mock.read.return_value = None

    custom_queue_func = MagicMock()

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    wf.SetCustomExecutorQueue(custom_queue_func)
    
    assert wf.WORKFLOW.custom_execution_queue == custom_queue_func

    wf.Call("a_step", "a_task")

    mock_enqueue.assert_called_once()


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_unsuccessful_step_and_retry_logic(mock_enqueue, mock_db):
    """
    A step that fails but has retries left should be re-enqueued.
    """
    db, db_mock = mock_db

    # Simulate a state where a step has failed but has retries
    existing_state = State(
        name="test_wf",
        run_id=789,
        steps=[Step(step_id=0, step_name="failing_step", task_key="failing_task", retries=1)],
        cache={},
    )
    db_mock.read.return_value = existing_state

    # Context indicating the step has been executed and completed, but was not successful
    context_json = json.dumps({
        "ids": [789, 0, -1],
        "executed": True,
        "completed": True,
        "success": False,
        "cache": {}
    })

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=context_json)

    # The workflow should not be waiting, as the step has completed (though unsuccessfully)
    assert not wf.WORKFLOW._is_waiting()

    # Calling the same step again should trigger a retry
    wf.Call("failing_step", "failing_task")

    # Assert that the task was enqueued again for a retry
    mock_enqueue.assert_called_once()
    assert wf.WORKFLOW.state.steps[0].retries == 0


@patch("switchboard.workflow.Workflow._enqueue_execution")
def test_out_of_retries(mock_enqueue, mock_db):
    """
    A step that is out of retries should not be re-enqueued.
    """
    db, db_mock = mock_db

    # Simulate a state where a step has failed and has no retries left
    existing_state = State(
        name="test_wf",
        run_id=789,
        steps=[Step(step_id=0, step_name="failing_step", task_key="failing_task", retries=0)],
        cache={},
    )
    db_mock.read.return_value = existing_state

    # Context indicating the step has been executed and completed, but was not successful
    context_json = json.dumps({
        "ids": [789, 0, -1],
        "executed": True,
        "completed": True,
        "success": False,
        "cache": {}
    })

    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=context_json)

    # The workflow should not be waiting
    assert not wf.WORKFLOW._is_waiting()

    # Calling the same step again should not trigger a retry
    wf.Call("failing_step", "failing_task")

    # Assert that the task was not enqueued again
    mock_enqueue.assert_not_called()


def test_GetCache_returns_current_state_cache(mock_db):

    db, db_mock = mock_db
    db_mock.read.return_value = None
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    assert(isinstance(wf.WORKFLOW, wf.Workflow))
    wf.WORKFLOW.state.cache = {"test_key": "test_value"}
    
    assert wf.GetCache() == {"test_key": "test_value"}


def test_Done_returns_200(mock_db):

    db, db_mock = mock_db
    db_mock.read.return_value = None
    
    wf.InitWorkflow(cloud=Cloud.CUSTOM, name="test_wf", db=db, context=NEW_WORKFLOW_CONTEXT)
    
    assert wf.Done() == 200