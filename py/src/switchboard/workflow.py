import json
from dataclasses import dataclass
from typing import Self





@dataclass
class Registry:
    # TODO 
    #   hammer out details of the schema
    contacts: dict


@dataclass
class Step:
    run_id: int
    name: str
    execution_type: str # make enum
    executed: bool = False
    completed: bool = False
    success: bool = False

@dataclass
class ParallelStep:
    tasks: list[Step] 



@dataclass
class State:
    steps: list[Step]
    run_id: int
    cache: dict = {} # cache can be used to store data that is pertinent to conditional steps in a workflow.


@dataclass
class Context:
    run_id: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict = {} # the context cache is used to add variables to the State cache



class WaitStatus:
    def call(self, *args, **kargs) -> Self:
        return self
    def parallel_call(self, *args, **kargs) -> Self:
        return self

# context = {
#             "run_id": [
#                 100, # workflow id
#                 1 # worker id
#             ],
#             "success" : True,
#             ...some other fields maybe...
#         }


class Workflow:
    _instance = None
    _initialized = False

    def __new__(cls, db, context) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db, context) -> None:
        if self._initialized:
            return

        self.step_idx = 0
        self.step_cnt = 0

        self.db = db
        self.context = self._get_context(context)
        self.state = self._init_state(db)

        self._initialized = True



    def _get_context(self, context) -> Context:
        raw = json.loads(context) 

        # required fields
        try:
            cntx = Context(raw["run_id"], raw["executed"], raw["completed"], raw["success"])
        except: 
            # newly triggered workflows wont have these fields
            cntx = Context([0,0], True, True, True)
        
        # optional fields
        if "cache" in raw:
            for k,v in raw["cache"]:
                cntx.cache[k] = v

        return cntx
        

    def _init_state(self, db) -> State:

        state = db.read(self.context.run_id[0])
        
        # handle new state creation (new workflow run)
        if not state:
            id = self._generate_id(db)
            state = State([], id)
            self.context.run_id[0] = id 
            return state

        assert state.steps
        if self.context.executed:
            state.steps[-1].executed = True
        if self.context.completed:
            state.steps[-1].completed = True
        if self.context.success:
            state.steps[-1].success = True
        
        for k,v in self.context.cache:
            state.cache[k] = v
        
        self.step_idx = len(state.steps)-1

        return state

    def _add_step(self, step):
        self.step_idx += 1
        self.state.steps.append(step)
    
    def _update_db(self, db):
        db.write(self.state.run_id, self.state)
        
    def _generate_id(self,db) -> int:
        return db.increment_id()

    def _generate_worker_id(self) -> int:
        return self.context.run_id[1]+1

    def _needs_retry(self) -> bool:
        if self.context.executed and self.context.completed and not self.context.success:
            return True
        return False

    def _is_waiting(self) -> bool:
        if self.context.executed and self.context.completed and self.context.success:
            return False
        return True 

    def _determine_step_execution(self, name, fn) -> bool:
        if not self._is_waiting():
            self._add_step(Step(self._generate_worker_id(), name, fn))
            return True
        if self._needs_retry():
            return True
        return False

    def _enqueue_execution(self, fn):
        print(f"Enqueuing function call: {fn['id']}")

        # Example message schema
        # queue.send_message({
        #     "function_id": fn["id"],
        #     "execution_type": "http"
        # })

    def _next(self) -> Self:
        self.step_cnt += 1
        return self

    def call(self, fn) -> Self | WaitStatus:
        if self._determine_step_execution("call", fn):
            # walk through orchestration steps until we are at current call
            if self.step_cnt != self.step_idx:
                return self._next()
            
            self._enqueue_execution(fn)
        
        self._update_db(self.db)
        return WaitStatus()

    def parallel_call(self, functions) -> Self | WaitStatus:
        wf = self
        for fn in functions:
            wf = self.call(fn)
        return wf
    
    def done(self):
        return





WORKFLOW = None
def NewWorkflow(db, context):
    global WORKFLOW
    WORKFLOW = Workflow(db, context)

def Call(fn):
    global WORKFLOW
    if WORKFLOW:
        WORKFLOW = WORKFLOW.call(fn)
    else:
        raise RuntimeError("Call used without an active workflow.")

def ParallelCall(functions):
    global WORKFLOW
    if WORKFLOW:
        WORKFLOW = WORKFLOW.parallel_call(functions)
    else:
        raise RuntimeError("Call used without an active workflow.")

def WaitCompleted(run_id):
    pass

