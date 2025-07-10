import pytest
from unittest.mock import patch
from switchboard.enums import Status, Cloud, StepType, SwitchboardComponent, TableName
from switchboard.schemas import State, Context, Step, ParallelStep
from switchboard.workflow import WORKFLOW, ClearWorkflow, WaitStatus, Workflow, InitWorkflow, Call, ParallelCall
from switchboard.db import DBInterface, DB




# mocks
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

    def get_endpoint(self, name: str, component: SwitchboardComponent) -> str:
        return "mocked/endpoint"

    def increment_id(self, name):
        self.id_max += 1
        return self.id_max

    def get_table(self, table: TableName):
        pass


    





# fixtures
@pytest.fixture(autouse=True)
def reset_workflow_singleton():
    global WORKFLOW
    if WORKFLOW:
        ClearWorkflow(Cloud.CUSTOM, 'clear', DB(Cloud.CUSTOM, DBMockInterface(None)), Context([1,0,-1], True, True, True,{})
)



# TODO
#   Add tests for use of the cache
#   Add tests for Parallel calls


@pytest.mark.parametrize(
        "name,state,context,expected_state,expected_context",
        [
            (
                "1. Start a brand new workflow.", 
                None, 
                '{"ids": [-1,-1,-1], "executed": true, "completed": true, "success": true}, "cache": {}', 
                State('test',1,[],{}), 
                Context([1,0,-1], True, True, True,{})
            ),
            (
                "2. Workflow after executing a worker.", 
                State('test',100,[Step(1,"step1","task1",True,False,False)],{}), 
                '{"ids": [100,1,-1], "executed": true, "completed": false, "success": false, "cache": {}}',
                State('test',100,[Step(2,"step2","task2",True,False,False)],{}),
                Context([100,1,-1], True, False, False,{})
            )

        ]
)
def test_new_Workflow(name, state, context, expected_state, expected_context):
    db = DB(Cloud.CUSTOM,DBMockInterface(state))
    wf = Workflow(Cloud.CUSTOM, 'test', db, context)

    assert wf.state == expected_state
    assert wf.context == expected_context

@pytest.mark.parametrize(
        "name,context,expected",
        [
            (
                "1. New Context.",
                '{"ids": [-1,-1,-1], "executed": true, "completed": true, "success": true, "cache": {}}',
                Context([0,0,-1], True, True, True,{})
            ),
            (
                "2. Non empty context.",
                '{"ids": [100,1,-1], "executed": true, "completed": true, "success": true, "cache": {}}',
                Context([100,1,-1], True, True, True,{})
            ),
            (
                "3. Parallel task context.",
                '{"ids": [100,2,0], "executed": true, "completed": true, "success": true, "cache": {}}',
                Context([100,2,0], True, True, True,{})
            ),
            # (
            #     "TODO - handle an invalid context",
            #     '{"ids": [100,1], "executed": true, "completed": False, "success": true}',
            #     Context([100,1], True, False, True)
            # ),
        ]
)
def test_get_context(name, context, expected):
    db = DB(Cloud.CUSTOM, DBMockInterface(None))
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',db,context)
    actual = wf._get_context(context) 
    assert actual == expected

def test_init_state(): 
    db = DB(Cloud.CUSTOM, DBMockInterface(State('test',100,[Step(1,"step1","task1",True,True,True), Step(2,"step2","task2",True,False,False)],{})))
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',db,'{}')
    wf.name = 'test'
    wf.context = Context([100,2,-1], True, True, True,{}) 
    expected = State('test',100,[Step(1,"step1","task1",True,True,True), Step(2,"step2","task2",True,False,False)],{})
    actual = wf._init_state(db.interface)
    assert actual == expected

def test_add_step():
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    wf.context = Context([1,0,-1], True, True, True,{}) 
    wf.state = State('test',1,[],{})
    wf.step_idx = 0
    wf._add_step(StepType.Call, "step1", "task1")
    wf.context = Context([1,1,-1], True, True, True,{}) 
    wf._add_step(StepType.Call, "step2", "task2")
    expected = State('test',1,[Step(1,"step1","task1",False,False,False), Step(2,"step2","task2",False,False,False)],{}) 
    actual = wf.state
    assert actual == expected

def test_generate_worker_id(): 
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    wf.context = Context([100,1], True, True, True,{})
    expected = 2
    actual = wf._generate_step_id()
    assert actual == expected

def test_needs_retry():
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    context = Context([100,1,-1], True, True, False,{})
    wf.context = context
    expected = True
    actual = wf._needs_retry(StepType.Call, Step(1,"step1","task1",True,True,False,retries=2))
    assert actual == expected

def test_is_waiting():
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    context = Context([100,1], True, False, False,{})
    wf.context = context
    expected = True
    actual = wf._is_waiting()
    assert actual == expected

def test_determine_step_execution():
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    wf.step_idx = -1
    wf.state = State('test',1,[],{})
    wf.context = Context([-1,-1,-1], False, False, False,{})
    expected = False
    actual = wf._determine_step_execution(StepType.Call, "step1", "task1")
    assert actual == expected
    
def test_next():
    wf = Workflow.__new__(Workflow, Cloud.CUSTOM, 'test',DB(Cloud.CUSTOM, DBMockInterface(None)),'')
    wf.step_cnt = 0
    actual = wf._next('step2', 'task2')
    assert actual == wf
    assert actual.step_cnt == 1









