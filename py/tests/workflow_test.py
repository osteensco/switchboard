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



def test_new_Workflow():
    context = '{}'
    db = DBMock(None)
    wf = Workflow(db, context)
    expected_context = Context([1,0], True, True, True)
    expected_state = State([],1)
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
    db = DBMock(None)
    wf = Workflow.__new__(Workflow)
    expected = 1
    actual = wf._generate_id(db)
    assert actual == expected

def test_needs_retry():
    wf = Workflow.__new__(Workflow)
    context = Context([100,1], True, True, False)
    wf.context = context
    expected = True
    actual = wf._needs_retry()
    assert actual == expected

def test_is_waiting():
    wf = Workflow.__new__(Workflow)
    context = Context([100,1], True, False, False)
    wf.context = context
    expected = True
    actual = wf._is_waiting()
    assert actual == expected

def test_enqueue_function():
    pass

def test_next():
    wf = Workflow.__new__(Workflow)
    wf.step_cnt = 0
    actual = wf._next()
    assert actual == wf
    assert actual.step_cnt == 1


def test_call():
    pass





