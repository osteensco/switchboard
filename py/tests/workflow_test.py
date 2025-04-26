from switchboard.workflow import State, Workflow, Context, Step



class DBMock: 
    def __init__(self, state: State | None) -> None:
        self.state = state if state else None

    def read(self, *args):
        return self.state

    def write(self, *args):
        return self.state


def test_new_Workflow():
    context = '{}'
    db = DBMock(None)
    wf = Workflow(db, context)
    expected_context = Context([0,0], True, True, True)
    expected_state = State([],0)
    assert wf.context == expected_context
    assert wf.state == expected_state

def test_get_context():
    wf = Workflow.__new__(Workflow)
    context = '{"run_id": [100,1], "executed": true, "completed": true, "success": true}'
    expected = Context([100,1], True, True, True)
    actual = wf._get_context(context) 
    assert actual == expected

def test_init_state(): 
    context = Context([100,2], True, True, True)
    expected = State([Step([100,1],"call","http",True,True,True), Step([100,2],"call","http",True,True,True)],100)
    db = DBMock(expected)
    wf = Workflow.__new__(Workflow)
    wf.context = context
    actual = wf._init_state(db)
    assert actual == expected

def test_add_step():
    wf = Workflow.__new__(Workflow)
    wf.step_idx = 0
    wf.state = State([],100)
    wf._add_step(Step([100,1],"call","http",True,True,True))
    wf._add_step(Step([100,2],"call","http",True,True,True))
    expected = State([Step([100,1],"call","http",True,True,True), Step([100,2],"call","http",True,True,True)],100) 
    actual = wf.state
    assert actual == expected

def test_generate_id():
    pass

def test_needs_retry():
    wf = Workflow.__new__(Workflow)
    context = Context([100,1], True, True, False)
    wf.context = context


def test_is_waiting():
    pass

def test_enqueue_function():
    pass

def test_next():
    pass

def test_call():
    pass





