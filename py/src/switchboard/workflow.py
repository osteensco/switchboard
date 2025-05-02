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
    step_id: int
    name: str
    execution_type: str # make enum
    executed: bool = False
    completed: bool = False
    success: bool = False
    task_id: int = -1


@dataclass
class ParallelStep:
    step_id: int
    tasks: list[Step] 
    executed: bool = False
    completed: bool = False
    success: bool = False


@dataclass
class State:
    steps: list[Step|ParallelStep]
    run_id: int
    cache: dict # cache can be used to store data that is pertinent to conditional steps in a workflow.


@dataclass
class Context:
    ids: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict # the context cache is used to add variables to the State cache

# context = {
#             "ids": [
#                 100, # run id
#                 1 # step id
#                 -1 # task id
#             ],
#             "success" : True,
#             ...etc...
#         }





class WaitStatus:
    def __init__(self, status) -> None:
        self.status = status

    def call(self, *args, **kargs) -> Self:
        return self

    def parallel_call(self, *args, **kargs) -> Self:
        return self

    def done(self) -> None:
        # TODO
        #   change return type to status codes
        return self.status





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
        self.curr_step = None
        self.status = "InProcess"

        self.db = db
        self.context = self._get_context(context)
        self.state = self._init_state(db)

        self._initialized = True


    @classmethod
    def _reset(cls):
        cls._instance = None
        cls._initialized = False


    @staticmethod
    def _get_context(context) -> Context:
        raw = json.loads(context) 

        try:
            # required fields
            cntx = Context(raw["ids"], raw["executed"], raw["completed"], raw["success"], {})
            assert 2 <= len(cntx.ids) <= 3
        except: 
            # newly triggered workflows wont have these fields
            cntx = Context([0,0,-1], True, True, True, {})
        
        # optional fields
        if "cache" in raw:
            for k,v in raw["cache"].items():
                cntx.cache[k] = v

        if len(cntx.ids) == 2:
            cntx.ids.append(-1)

        return cntx


    def _init_state(self, db) -> State:
        '''
        Get the state from the database and update it based on the current context.
        '''

        state = db.read(self.context.ids[0])
        
        # handle new state creation (new workflow run)
        if not state:
            id = self._generate_id(db)
            state = State([], id, {})
            self.context.ids[0] = id 
            return state
        
        # if we already have an initialized state it should never be emtpy
        assert state.steps
        
        for k,v in self.context.cache:
            state.cache[k] = v
        
        self.step_idx = len(state.steps)-1
        self.curr_step = state.steps[self.step_idx]
        
        # handle context from a task in a ParallelStep vs Step
        if self.context.ids[2] >= 0:
            assert isinstance(self.curr_step, ParallelStep)
            executed = True
            completed = True
            success = True

            # we ingest the context from an individual task, but need to analyze it within the context of the whole set of parallel tasks            
            for task in self.curr_step.tasks:
                if task.task_id == self.context.ids[2]:
                    if self.context.executed:
                        task.executed = True
                    if self.context.completed:
                        task.completed = True
                    if self.context.success:
                        task.success = True

                if not executed and not completed and not success:
                    continue

                executed = False if not task.executed else executed
                completed = False if not task.completed else completed
                success = False if not task.success else success

            self.curr_step.executed, self.context.executed = executed, executed
            self.curr_step.completed, self.context.completed = completed, completed
            self.curr_step.success, self.context.success = success, success
                
        else:
            assert isinstance(self.curr_step, Step)
            if self.context.executed:
                self.curr_step.executed = True
            if self.context.completed:
                self.curr_step.completed = True
            if self.context.success:
                self.curr_step.success = True

        return state


    def _add_step(self, name, *fn):
        if name == "parallel":
            step_id = self._generate_worker_id()
            task_id = 0
            tasks = []
            for f in fn:
                tasks.append(Step(step_id,"call",f,task_id=task_id))
                task_id += 1
            self.state.steps.append(ParallelStep(step_id, tasks))
        else:
            self.state.steps.append(Step(self._generate_worker_id(), name, fn[0]))

        self.step_idx += 1
        self.curr_step = self.state.steps[self.step_idx]


    def _update_db(self, db):
        db.write(self.state.run_id, self.state)

    
    @staticmethod
    def _generate_id(db) -> int:
        return db.increment_id()


    def _generate_worker_id(self) -> int:
        return self.context.ids[1]+1


    def _needs_retry(self) -> bool:
        # TODO
        #   check number of retries allowed and executed
        #   update the db if a retry is required so the state reflects number of retries sent
        if self.context.executed and self.context.completed and not self.context.success:
            return True
        # if out of retries:
        #     self.status = "OutOfRetries"
        return False


    def _is_waiting(self) -> bool:
        if self.context.executed and self.context.completed and self.context.success:
            return False
        return True 


    def _determine_step_execution(self, name: str, *fn: str) -> bool:
        if not self._is_waiting():
            self._add_step(name, *fn)
            return True
        if self._needs_retry():
            return True
        return False

    
    @staticmethod
    def _enqueue_execution(fn):
        print(f"Enqueuing function call: {fn}")

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
            
            # we don't need to update the db until after a successful execution
            self._enqueue_execution(fn)
        
        # when we determine the step doesn't need to be executed then the db just needs to be updated
        self._update_db(self.db)
        return WaitStatus(self.status)


    def parallel_call(self, *functions) -> Self | WaitStatus:
        if self._determine_step_execution("parallel", *functions):
            assert isinstance(self.curr_step, ParallelStep)
            # walk through orchestration steps until we are at current call
            if self.step_cnt != self.step_idx:
                return self._next()
            
            # we don't need to update the db until after a successful execution
            for fn in functions:
                self._enqueue_execution(fn)
        
        # when we determine the step doesn't need to be executed then the db just needs to be updated
        self._update_db(self.db)
        return WaitStatus(self.status)


    def done(self):
        if self.status == "InProcess":
            self.status = "Completed"
        return self.status





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
        raise RuntimeError("ParallelCall used without an active workflow.")



