import json
from typing import Self

from .db import DB, DBInterface
from .executor import push_to_executor
from .schemas import State, Step, ParallelStep, Context 
from .enums import Cloud, Status, StepType




#TODO
#   add logging and log sink



class WaitStatus:
    def __init__(self, status: Status, state: State) -> None:
        self.status = status
        self.state = state

    def call(self, *args, **kargs) -> Self:
        return self

    def parallel_call(self, *args, **kargs) -> Self:
        return self

    def done(self) -> int:
        # TODO
        #   log status
        return 200



class Workflow:
    _instance = None
    _initialized = False

    def __new__(cls, cloud: Cloud, name: str, db: DB, context: str) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cloud: Cloud, name: str, db: DB, context: str) -> None:
        if self._initialized:
            return
        
        self.cloud = cloud
        self.name = name
        self.step_idx = 0
        self.step_cnt = 0
        self.curr_step = None
        self.status = Status.InProcess

        self.db = db.interface
        self.context = self._get_context(context)
        self.state = self._init_state(self.db)

        self._initialized = True


    @classmethod
    def _reset(cls):
        cls._instance = None
        cls._initialized = False


    @staticmethod
    def _get_context(context: str) -> Context:
        '''
        Get the context from the request, ensuring all required fields are present.
        '''

        raw_context = json.loads(context) 

        # required fields
        assert "ids" in raw_context.keys(), "required field 'ids' not present in context."
        assert "executed" in raw_context.keys(), "required field 'executed' not present in context."
        assert "completed" in raw_context.keys(), "required field 'completed' not present in context."
        assert "success" in raw_context.keys(), "required field 'success' not present in context."

        cntx = Context(raw_context["ids"], raw_context["executed"], raw_context["completed"], raw_context["success"], {})
        assert len(cntx.ids) == 3, "context ids should have the run_id (0 idx), step_id (1 idx), and the task_id (2 idx)"

        # a newly triggered workflow will always have these ids exactly
        if cntx.ids == [-1,-1,-1]: 
            cntx = Context([0,0,-1], True, True, True, {})
        
        # optional fields
        if "cache" in raw_context:
            for k,v in raw_context["cache"].items():
                cntx.cache[k] = v

        # handle context without task id
        # task id is only required for a task as part of a ParallelStep

        if len(cntx.ids) == 2:
            cntx.ids.append(-1)

        return cntx


    def _init_state(self, db: DBInterface) -> State:
        '''
        Get the state from the database and update it based on the current context.
        '''

        state = db.read(self.name, self.context.ids[0])
        if state:
            assert isinstance(state, State) 
        else:
            # handle new state creation (new workflow run)
            id = self._generate_id(db)
            state = State(self.name, id, [], {})
            self.context.ids[0] = id 
            return state
        
        # if we already have an initialized state it should never be emtpy
        assert state.steps

        
        # keys can and should be overwritten in the cache
        # TODO 
        #   log when a key is overwritten in the cache
        for k,v in self.context.cache:
            state.cache[k] = v
        
        self.step_idx = len(state.steps)-1
        self.curr_step = state.steps[self.step_idx]
        
        # step id should always match our step id from the context
        assert self.curr_step.step_id == self.context.ids[1], f"step id mismatch, curr_step={self.curr_step.step_id} context={self.context.ids[1]}"

        #   We ignore invocations from an impossible context to ensure idempotence
        if self.curr_step.executed and not self.context.executed:
            return state
        if self.curr_step.completed and not self.context.completed:
            return state
        if self.curr_step.success and not self.context.success:
            return state


        # handle context from a task in a ParallelStep vs Step
        if self.context.ids[2] >= 0: # id at index 2 is the task id, which is -1 unless the step is part of a ParallelStep
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
            
            # the context referenced by the workflow will need to represent the ParallelStep as a whole
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


    def _add_step(self, name: StepType, *tasks):
        '''
        Add the next step to the state. Adding an additional step to the workflow state brings the assumption that it was attempted to be executed.
        The workflow state will not recognize that it's been executed until receiving a success response from the executor function.
        '''
        if name == StepType.Parallel:
            step_id = self._generate_step_id()
            task_id = 0
            tasks = []
            for t in tasks:
                tasks.append(Step(step_id,t,task_id=task_id))
                task_id += 1
            self.state.steps.append(ParallelStep(step_id, tasks))
        else:
            task = tasks[0]
            self.state.steps.append(Step(self._generate_step_id(), task))

        self.step_idx += 1
        self.curr_step = self.state.steps[self.step_idx]


    def _update_db(self, db: DBInterface):
        db.write(self.state)

    
    def _generate_id(self, db: DBInterface) -> int:
        return db.increment_id(self.name)


    def _generate_step_id(self) -> int:
        return self.context.ids[1]+1


    def _needs_retry(self, step_type: StepType, step: Step | ParallelStep | None) -> bool:
        assert step
        retries = 0
        if self.context.executed and self.context.completed and not self.context.success:
            match step_type:
                case StepType.Call:
                    assert isinstance(step, Step)
                    retries = step.retries
                    step.retries -= 1 # this will update the appropriate step in self.state
                case StepType.Parallel:
                    assert isinstance(step, ParallelStep)
                    found = False
                    for s in step.tasks:
                        if s.task_id == self.context.ids[2]:
                            found = True
                            retries = s.retries
                            s.retries -= 1 # this will update the appropriate step in self.state
                    assert found, "no task id matches the task id in the context - \ntasks={step.tasks}\ncontext={self.context}"
        if retries <= 0:
            return False
        return True


    def _is_waiting(self) -> bool:
        if self.context.executed and self.context.completed and self.context.success:
            return False
        return True 


    def _determine_step_execution(self, name: StepType, *tasks: str) -> bool:
        if not self._is_waiting():
            self._add_step(name, *tasks)
            return True
        if self._needs_retry(name, self.curr_step):
            return True
        return False

    
    @staticmethod
    def _enqueue_execution(cloud: Cloud, db: DBInterface, name: str, task: str):
        msg_body = json.dumps({"execute": task})
        resp = push_to_executor(cloud, db, name, msg_body)
        # TODO
        #   log response


    def _next(self) -> Self:
        self.step_cnt += 1
        return self


    def call(self, task) -> Self | WaitStatus:
        if self._determine_step_execution(StepType.Call, task):
            # walk through orchestration steps until we are at current call
            if self.step_cnt != self.step_idx:
                return self._next()
            
            # we don't need to update the db until after a successful execution
            self._enqueue_execution(self.cloud, self.db, self.name, task)
        
        # when we determine the step doesn't need to be executed then the db just needs to be updated
        self._update_db(self.db)
        return WaitStatus(self.status, self.state)


    def parallel_call(self, *tasks) -> Self | WaitStatus:
        if self._determine_step_execution(StepType.Parallel, *tasks):
            assert isinstance(self.curr_step, ParallelStep)
            # walk through orchestration steps until we are at current call
            if self.step_cnt != self.step_idx:
                return self._next()
            
            # we don't need to update the db until after a successful execution
            for task in tasks:

                self._enqueue_execution(self.cloud, self.db, self.name, task)
        
        # when we determine the step doesn't need to be executed then the db just needs to be updated
        self._update_db(self.db)
        return WaitStatus(self.status, self.state)


    def done(self):
        if self.status is Status.InProcess:
            self.status = Status.Completed
        # TODO
        #   log status
        return 200





WORKFLOW = None

# workflow interface decorator
def wf_interface(func):
    def nullcheck(*args, **kargs):
        global WORKFLOW
        if WORKFLOW:
            func(*args, **kargs)
        else:
            raise RuntimeError("Attempted to interact with the WORKFLOW without it being active. Make sure you call the InitWorkflow() function before calling this function.")
    return nullcheck





def InitWorkflow(cloud: Cloud, name: str, db: DB, context: str):
    '''
    Initialize the Workflow singleton. The Workflow acts as the orchestration engine for switchboard. 
        Args:
            cloud: The cloud provider being used. See switchboard.Cloud.
            name: The name of the Worflow. Used to differentiate between workflows in the database.
            db: The DB object. Must be initialized before passing in to the Workflow. See switchboard.DB.
            context: The context of the Workflow. This typically represents the step the Workflow needs to pick up at. See swithcboard.Context.
    '''
    global WORKFLOW
    WORKFLOW = Workflow(cloud, name, db, context)


@wf_interface
def Call(task: str) -> None:
    '''
    Call a task in a workflow.
    A task string must match a key in the directory_map located in tasks.py as part of the executor function.
    '''
    global WORKFLOW
    assert WORKFLOW is not None
    WORKFLOW = WORKFLOW.call(task)


@wf_interface
def ParallelCall(*tasks: str) -> None:
    '''
    Call a group of tasks that should run in parallel.
    The *tasks argument are strings that must match corresponding keys in the directory_map located in tasks.py as part of the executor function.
    '''
    global WORKFLOW
    assert WORKFLOW is not None
    WORKFLOW = WORKFLOW.parallel_call(*tasks)


@wf_interface
def GetCache() -> dict:
    '''
    Retrieve the switchboard cache. The switchboard cache is a simple dictionary used to pass information between tasks and your workflow orchestration.
    '''
    assert WORKFLOW is not None
    return WORKFLOW.state.cache


@wf_interface
def Done() -> int:
    '''
    Calling Done() signifies the end of a switchboard workflow. This function will return the status code of the workflows execution.
    '''
    assert WORKFLOW is not None
    return WORKFLOW.done()



