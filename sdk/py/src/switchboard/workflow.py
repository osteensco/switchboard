import json
from typing import Callable, Self

from .db import DB, DBInterface
from .executor import push_to_executor
from .schemas import State, Step, ParallelStep, Context 
from .enums import Cloud, Status, StepType
from .logging_config import log







class WaitStatus:
    """
    The WaitStatus class is a dummy object used to avoid execution of downstream tasks during execution of the main switchboard serverless function.
    """
    def __init__(self, status: Status, state: State) -> None:
        self.status = status
        self.state = state

    def call(self, *args, **kargs) -> Self:
        return self

    def parallel_call(self, *args, **kargs) -> Self:
        return self

    def done(self) -> int:
        print("!!!!!!!!! WaitStatus done called")
        return 200



class Workflow:
    """
    The main engine for Switchboard orchestrations.

    The Workflow class is a singleton that manages the state of a single workflow execution.
    It is responsible for initializing the workflow's state from a database,
    tracking the progress of steps, handling retries, and executing tasks.

    It is not meant to be instantiated directly. Instead, the `InitWorkflow` function
    should be used to create and initialize the singleton instance.
    """
    _instance = None
    _initialized = False

    def __new__(cls, cloud: Cloud, name: str, db: DB, context: str) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cloud: Cloud, name: str, db: DB, context: str) -> None:
        """
        Initializes the Workflow singleton.

        This constructor is called by the `__new__` method only when an instance
        of the Workflow does not yet exist. It sets up the initial state of the
        workflow based on the provided context.

        Args:
            cloud: The cloud provider being used (e.g., Cloud.AWS).
            name: The name of the workflow, used for identification in the database.
            db: An initialized DB object for state persistence.
            context: The JSON string context from the invocation event, which determines
                     the current state of the workflow.
        """
        if self._initialized:
            return
        
        self.custom_execution_queue = None
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
        log.bind(
            component="workflow_service", 
            workflow_name=name,
            context=context
        ).info("-- Workflow.__init__ executed. --")


    def _set_custom_execution_queue(self, custom_execution_queue_function: Callable):
        self.custom_execution_queue = custom_execution_queue_function


    @staticmethod
    def _get_context(context: str) -> Context:
        '''
        Get the context from the request, ensuring all required fields are present.
        '''

        raw_context = json.loads(context) 
        print(f"!!!!!!!!!!!!! - {raw_context}")
        # required fields
        assert "ids" in raw_context.keys(), "required field 'ids' not present in context."
        assert "executed" in raw_context.keys(), "required field 'executed' not present in context."
        assert "completed" in raw_context.keys(), "required field 'completed' not present in context."
        assert "success" in raw_context.keys(), "required field 'success' not present in context."
        assert "cache" in raw_context.keys(), "required field 'cache' not present in context."

        cntx = Context(raw_context["ids"], raw_context["executed"], raw_context["completed"], raw_context["success"], raw_context["cache"])
        assert len(cntx.ids) == 3, "context ids should have the run_id (0 idx), step_id (1 idx), and the task_id (2 idx)"

        # a newly triggered workflow will always have these ids exactly
        if cntx.ids == [-1,-1,-1]: 
            cntx = Context(cntx.ids, True, True, True, {})
        
        # optional fields
        if "cache" in raw_context:
            assert isinstance(raw_context["cache"], dict), "The 'cache' field should be a dictionary like object."
            for k,v in raw_context["cache"].items():
                cntx.cache[k] = v


        log.bind(
            component="workflow_service",
            context=context
        ).info("-- Context retrieved. --")
        
        return cntx


    def _init_state(self, db: DBInterface) -> State:
        '''
        Get the state from the database and update it based on the current context.
        '''

        state = db.read(self.name, self.context.ids[0])
        if state:
            print(f"!!!!!! found state={state}")
            assert isinstance(state, State) 
        else:
            print(f"!!!!! could not find name={self.name}, run_id={self.context.ids[0]}, state={state}")
            # handle new state creation (new workflow run)
            id = self._generate_id(db)
            state = State(self.name, id, [], {})
            self.context.ids[0] = id 
            return state
        
        # if we already have an initialized state it should never be emtpy
        assert state.steps

        
        # keys can and should be overwritten in the cache
        for k,v in self.context.cache.items():
            if k in state.cache:
                log.bind(
                    state=state,
                    context=self.context
                ).debug(f"-- key {k} overwritten in the cache. --")
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

            # we ingest the context from an individual task, but need to analyze it within the context of the whole set of parallel tasks
            # first we update the status in the task located in the curr_step
            for task in self.curr_step.tasks:
                if task.task_id == self.context.ids[2]:
                    if self.context.executed:
                        task.executed = True
                    if self.context.completed:
                        task.completed = True
                    if self.context.success:
                        task.success = True
                    break

            # we then compare against all other tasks and update the curr_step and context appropriately
            executed = []
            completed = []
            success = []
            for task in self.curr_step.tasks:
                executed.append(task.executed)
                completed.append(task.completed)
                success.append(task.success)
            
            self.curr_step.executed = min(executed)
            self.context.executed = self.curr_step.executed
            self.curr_step.completed = min(completed)
            self.context.completed = self.curr_step.completed
            self.curr_step.success = min(success)
            self.context.success = self.curr_step.success
                
        else:
            assert isinstance(self.curr_step, Step)
            if self.context.executed:
                self.curr_step.executed = True
            if self.context.completed:
                self.curr_step.completed = True
            if self.context.success:
                self.curr_step.success = True

        log.bind(
            component="workflow_service",
            context=self.context,
            state=state
        ).info("-- State retrieved. --")

        return state


    def _add_step(self, type: StepType, step_name: str, *tasks):
        '''
        Add the next step to the state. Adding an additional step to the workflow state brings the assumption that it was attempted to be executed.
        The workflow state will not recognize that it's been executed until receiving a success response from the executor function.
        '''

        assert self.step_idx == max(len(self.state.steps)-1,0), f"The step_idx is incorrect, step_id: {self.step_idx}, state.steps: {self.state.steps}"
        if type == StepType.Parallel:
            step_id = self._generate_step_id()
            task_id = 0
            parallel_tasks = []
            for t in tasks:
                parallel_tasks.append(Step(step_id, step_name, t, task_id=task_id))
                task_id += 1
            self.state.steps.append(ParallelStep(step_id, step_name, parallel_tasks))
        else:
            task = tasks[0]
            self.state.steps.append(Step(self._generate_step_id(), step_name, task))
        
        self.curr_step = self.state.steps[self.step_cnt]
        
        # at this point we have officially transitioned from one step to the next
        # context has to be updated here to ensure state accuracy moving forward
        self.context = Context([self.state.run_id, self.curr_step.step_id, -1], False, False, False, self.context.cache)

        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            step_id=self.curr_step.step_id,
            step_name=step_name,
            context=self.context
        ).info("-- Step added to workflow state. --")


    @classmethod
    def _reset_singleton(cls):
        cls._instance = None
        cls._initialized = False


    def _update_db(self, db: DBInterface):
        assert self.curr_step is not None
        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            context=self.context,
            state=self.state
        ).info("-- State written to database. --")
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
        waiting = True
        if self.context.completed:
            waiting = False

        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            context=self.context
        ).debug(f" -- _is_waiting()={waiting} -- ")
        
        return waiting

    def _determine_step_execution(self, type: StepType, step_name: str, *tasks: str) -> bool:
        '''
        Helps determine if a step should be added and executed. Handles addition of the step.
        '''

        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            context=self.context,
            step_name=step_name,
            tasks=tasks
        ).info("-- Determining step execution. --")

        # We can only add a new step if we are not waiting for a previous one to complete.
        if self._is_waiting():
            return False

        # Check if the step has already been processed or is the current one.
        step_already_exists = False
        for step in self.state.steps:
            if step.step_name == step_name:
                step_already_exists = True
                break
        print(f"!!!!!!!!!!!!!!!! -- step_already_exists: {step_already_exists}, step_name: {step_name}")
        if step_already_exists:
            # We only execute it if it's the current step and needs a retry.
            # Otherwise, we are either waiting for it or it's already done.
            if self.curr_step and self.curr_step.step_name == step_name:
                if self._needs_retry(type, self.curr_step):
                    return True

        else:
            self._add_step(type, step_name, *tasks)
            return True
        
        return False

    
    def _enqueue_execution(self, cloud: Cloud, db: DBInterface, name: str, task: str, task_id: int = -1):
        assert self.curr_step, "There should be a curr_step populated for the Workflow object when _enqueue_execution() is called."
        # the task and the workflow name needs to be added to the context at this point
        # TODO
        #   - 'workflow' should probably just be a field in the Context object

        # task_id has to be added here in order to handle parallel tasks
        self.context.ids[2] = task_id
        msg_body = json.dumps({"workflow": name, "execute": task} | self.context.to_dict())
        log.bind(
            component="workflow_service",
            workflow_name=name,
            run_id=self.state.run_id,
            step_name=self.curr_step.step_name,
            context=self.context,
            task_key=task,
            message=msg_body
        ).info("-- Enqueuing task for execution. --")
        
        resp = push_to_executor(cloud, db, name, msg_body, self.custom_execution_queue)
        
        log.bind(
            component="workflow_service",
            workflow_name=name,
            run_id=self.state.run_id,
            step_name=self.curr_step.step_name,
            task_key=task,
            enqueue_response=resp
        ).info("-- Enqueue Response received. --")


    def _next(self, step_name, *tasks) -> Self:
        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            step_name=step_name,
            tasks=tasks,
            step_cnt=self.step_cnt,
            step_idx=self.step_idx
        ).info("-- Call passing to the next step node. --")

        self.step_cnt += 1
        return self


    def call(self, step_name: str, task: str) -> Self | WaitStatus:
        """
        Executes a single task as a step in the workflow.

        This method determines if the task needs to be executed, retried, or skipped.
        If execution is required, it enqueues the task for the executor.
        If the workflow is waiting for a task to complete, it returns a WaitStatus
        object to halt further execution of the orchestration logic.

        Args:
            task: The name of the task to execute. This must correspond to a key
                  in the executor's directory_map.

        Returns:
            The Workflow instance to allow for method chaining, or a WaitStatus
            object if the workflow should pause.
        """

        print(f"!!!!!!!!!!!! -- step_cnt: {self.step_cnt}, step_idx: {self.step_idx}")
        if self.step_cnt < self.step_idx:
            return self._next(step_name, task)

        if self._determine_step_execution(StepType.Call, step_name, task):
            # walk through orchestration steps until we are at current call
            # if self.step_cnt != self.step_idx:
            #     log.bind(
            #         component="workflow_service",
            #         workflow_name=self.name,
            #         run_id=self.state.run_id,
            #         step_name=step_name
            #     ).debug(f" -- step_cnt={self.step_cnt}, step_idx={self.step_idx} -- ")
            #
            #     return self._next(step_name, task)
            
            # we don't need to update the db until after a successful execution
            self._enqueue_execution(self.cloud, self.db, self.name, task)
        
        # this handles the first step being completed, which would miss on the step_idx logic check above
        elif self.curr_step and self.curr_step.success:
            return self._next(step_name, task)

        # when we determine the step doesn't need to be executed then the db just needs to be updated
        print(f"DEBUG: Before _update_db in call() - type(self.state.steps): {type(self.state.steps)}")
        if self.state.steps:
            print(f"DEBUG: Before _update_db in call() - type(self.state.steps[0]): {type(self.state.steps[0])}")
        self._update_db(self.db)

        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            step_name=step_name
        ).info("-- Returning WaitStatus from call() execution. --")
        return WaitStatus(self.status, self.state)


    def parallel_call(self, step_name: str, *tasks: str) -> Self | WaitStatus:
        """
        Executes multiple tasks in parallel as a single step in the workflow.

        This method determines if the group of tasks needs to be executed. If so,
        it enqueues all tasks for the executor. The workflow will wait for all
        tasks in the parallel step to complete before proceeding.

        Args:
            *tasks: A list of task names to execute in parallel. Each name must
                    correspond to a key in the executor's directory_map.

        Returns:
            The Workflow instance to allow for method chaining, or a WaitStatus
            object if the workflow should pause.
        """
        if self.step_cnt < self.step_idx:
            return self._next(step_name, *tasks)

        if self._determine_step_execution(StepType.Parallel, step_name, *tasks):
            assert isinstance(self.curr_step, ParallelStep)
            
            for task_key in tasks:
                task_id = None

                # TODO
                #   - implement a better search algorithm to grab the task_id
                #       - or redesign this so that the task id is updated in the context
                #       - or a context object is passed to _enqueue_execution
                for task in self.curr_step.tasks: 
                    if task.task_key == task_key:
                        task_id = task.task_id
                        break
                assert task_id != None, f"task_id was not found in parallel_call - tasks(arg): {tasks}, curr_step.tasks: {[task.task_key for task in self.curr_step.tasks]}"
                self._enqueue_execution(self.cloud, self.db, self.name, task_key, task_id)
        
        elif self.curr_step and self.curr_step.success:
            return self._next(step_name, *tasks)
        
        # we don't need to update the db until after a successful execution
        # when we determine the step doesn't need to be executed then the db just needs to be updated
        print(f"DEBUG: Before _update_db in parallel_call() - type(self.state.steps): {type(self.state.steps)}")
        if self.state.steps:
            print(f"DEBUG: Before _update_db in parallel_call() - type(self.state.steps[0]): {type(self.state.steps[0])}")
        self._update_db(self.db)

        log.bind(
            component="workflow_service",
            workflow_name=self.name,
            run_id=self.state.run_id,
            step_name=step_name
        ).info("-- Returning WaitStatus from parallel_call() execution. --")
        return WaitStatus(self.status, self.state)


    def done(self):
        """
        Marks the workflow as completed.

        This should be the final call in a workflow definition. It finalizes the
        workflow's status.

        Returns:
            An integer status code (e.g., 200) to indicate completion.
        """
        if self.status is Status.InProcess:
            self.status = Status.Completed
            log.bind(
                component="workflow_service",
                workflow_name=self.name,
                run_id=self.state.run_id
            ).info("-- Workflow marked as completed. --")
        # Database needs to be updated one last time
        self._update_db(self.db)

        return 200






WORKFLOW = None


def wf_interface(func):
    """
    Ensures that the Workflow singleton is initialized before calling a public interface function.

    This decorator acts as a guard for all public functions that interact with the
    global `WORKFLOW` instance. It checks if the singleton has been instantiated via
    `InitWorkflow()` and raises a `RuntimeError` if it has not. This prevents
    errors from trying to use the workflow engine before it's ready.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function, which will perform the check before execution.

    Raises:
        RuntimeError: If the `WORKFLOW` singleton is not initialized.
    """
    def nullcheck(*args, **kargs):
        global WORKFLOW
        if WORKFLOW:
            return func(*args, **kargs)
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
    if WORKFLOW:
        log.bind(
            component="workflow_service", 
            workflow_name=name,
            context=context
        ).debug("-- WORKFLOW singleton already exists! --")
    WORKFLOW = Workflow(cloud, name, db, context)
    log.bind(
        component="workflow_service", 
        workflow_name=name,
        context=context
    ).info("-- Workflow initialized. --")
    print("!!!!!!! - workflow: ", WORKFLOW)

@wf_interface
def SetCustomExecutorQueue(executor_queue_function: Callable):
    global WORKFLOW
    assert WORKFLOW is not None
    assert not isinstance(WORKFLOW, WaitStatus)
    WORKFLOW._set_custom_execution_queue(executor_queue_function)

@wf_interface
def Call(step_name, task: str) -> None:
    '''
    Call a task in a workflow.
    A task string must match a key in the directory_map located in tasks.py as part of the executor function.
    '''
    print(f"!!!!!!!! -- calling task `{task}`")
    global WORKFLOW
    assert WORKFLOW is not None
    WORKFLOW = WORKFLOW.call(step_name, task)


@wf_interface
def ParallelCall(step_name, *tasks: str) -> None:
    '''
    Call a group of tasks that should run in parallel.
    The *tasks argument are strings that must match corresponding keys in the directory_map located in tasks.py as part of the executor function.
    '''
    global WORKFLOW
    assert WORKFLOW is not None
    WORKFLOW = WORKFLOW.parallel_call(step_name, *tasks)


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
    status = WORKFLOW.done()
    Workflow._reset_singleton()
    return status



