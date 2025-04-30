import pytest
from switchboard.workflow import State, Workflow, Context, Step



class DBMock: 
    def __init__(self, state: State | None) -> None:
        self.all_states, self.id_max = self._prepopulate(state)

    def _prepopulate(self, state: State | None) -> tuple[dict, int]:
        if state:
            return {state.run_id: state}, state.run_id
        return {}, 0
        
    def read(self, id):
        try:
            state = self.all_states[id]
            return state
        except KeyError:
            return None

    def write(self, id, state):
        self.all_states[id] = state

    def increment_id(self):
        self.id_max += 1
        return self.id_max



# TODO
#   Add tests including use of the cache
#   Fix tests to account for singleton approach 



@pytest.mark.parametrize(
        "name,db,context,expected_state,expected_context",
        [
            (
                "1. Start a brand new workflow.", DBMock(None), '{}', State([],1), Context([1,0], True, True, True)
            ),
            (
                "2. Workflow after executing a worker.", 
                DBMock(State([Step(1,"call","http",True,False,False)],100)), 
                '{"run_id":[100,1],"executed": true, "completed": false, "success": false }',
                State([Step(1,"call","http",True,False,False)],100),
                Context([100,1], True, False, False)
            )

        ]
)
def test_new_Workflow(name, db, context, expected_state, expected_context):
    wf = Workflow(db, context)
    assert wf.state == expected_state
    assert wf.context == expected_context

@pytest.mark.parametrize(
        "name,context,expected",
        [
            (
                "1. Empty context.",
                '{}',
                Context([0,0], True, True, True)
            ),
            (
                "2. Non empty context.",
                '{"run_id": [100,1], "executed": true, "completed": true, "success": true}',
                Context([100,1], True, True, True)
            ),
            # (
            #     "3. Invalid context.",
            #     '{"run_id": [100,1], "executed": true, "completed": False, "success": true}',
            #     Context([100,1], True, False, True)
            # ),
        ]
)
def test_get_context(name, context, expected):
    db = DBMock(None)
    wf = Workflow.__new__(Workflow,db,context)
    actual = wf._get_context(context) 
    assert actual == expected

def test_init_state(): 
    context = Context([100,2], True, True, True)
    expected = State([Step(1,"call","http",True,True,True), Step(2,"call","http",True,True,True)],100)
    db = DBMock(expected)
    wf = Workflow.__new__(Workflow,db,context)
    wf.context = context
    actual = wf._init_state(db)
    assert actual == expected

def test_add_step():
    wf = Workflow.__new__(Workflow,None,None)
    wf.step_idx = 0
    wf.state = State([],100)
    wf._add_step(Step(1,"call","http",True,True,True))
    wf._add_step(Step(2,"call","http",True,True,True))
    expected = State([Step(1,"call","http",True,True,True), Step(2,"call","http",True,True,True)],100) 
    actual = wf.state
    assert actual == expected

def test_generate_worker_id(): 
    wf = Workflow.__new__(Workflow,None,None)
    wf.context = Context([100,1], True, True, True)
    expected = 2
    actual = wf._generate_worker_id()
    assert actual == expected

def test_needs_retry():
    wf = Workflow.__new__(Workflow,None,None)
    context = Context([100,1], True, True, False)
    wf.context = context
    expected = True
    actual = wf._needs_retry()
    assert actual == expected

def test_is_waiting():
    wf = Workflow.__new__(Workflow,None,None)
    context = Context([100,1], True, False, False)
    wf.context = context
    expected = True
    actual = wf._is_waiting()
    assert actual == expected

def test_determine_step_execution():
    wf = Workflow.__new__(Workflow,None,None)
    wf.step_idx = 0
    wf.state = State([],100)
    wf.context = Context([100,1], True, True, True)
    expected = True
    actual = wf._determine_step_execution("call", "test")
    assert actual == expected
    
def test_next():
    wf = Workflow.__new__(Workflow,None,None)
    wf.step_cnt = 0
    actual = wf._next()
    assert actual == wf
    assert actual.step_cnt == 1

def test_call():
    wf = Workflow.__new__(Workflow,None,None)
    wf.step_cnt = 0
    wf.step_idx = 0
    wf.state = State([],100)
    wf.context = Context([100,1], True, True, True)
    actual = wf.call("test")
    assert actual == wf





