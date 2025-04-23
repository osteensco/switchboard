from dataclasses import dataclass


@dataclass
class Registry:
    function: str
    trigger: str # or enum?
    contact: dict # or obj?


class Step:
    def __init__(self, id, name, fn) -> None:
        self.id = id if id else self._generate_id()
        self.name = name
        self.fn = fn
        self.success = False

    def _generate_id(self) -> int:
        return 0


@dataclass
class State:
    steps: list[Step]
    run_id: int


class Workflow:
    def __init__(self, db, context) -> None:
        self.step_idx = 0
        self.step_cnt = 0
        self.state = self._init_state(db,)
        self.run_id = self._get_run_id(self.state)
        self.steps = self.state["steps"]
        self.context = self._get_context(context)

        # workflow is stepped through by tracking the index (number of steps completed) and current count (current index in steps)
        # TODO
        #   - setup caching for conditionals, loops, etc
        #   - ENUMS?

        # read in context and state
        # create new run_id if we don't have one
        # populate known steps based on the state
        # determine step_idx based on len of known steps
        # for any public method call, we need to determine if that step has been executed based on step idx vs cnt comparison
        # if it hasn't been executed, we push to the queue
        # if we are on the most recently identified step, we need to check if it was successful
        # verify run_id is not marked as complete (this should never occur but an important assertion to make)

    def _get_context(self, context):
        if not context.run_id:
            # generate run_id
            return
        if context.success:
            self.steps[-1]["success"] = True
        else:
            pass
            # apply retry logic
            # retry logic should have a default and be defined by the user
        
        return

    def _init_state(self, db):
        state = {"steps": [], "run_id": self.run_id}
        # read state from db
        self.step_idx = len(state)-1
        return state

    def _update_state(self, step):
        self.step_idx += 1
        self.state["steps"]
    
    def _update_db(self, db):
        # write self.state to db using run_id
        pass
    
    def _get_run_id(self, state):
        pass

    def _determine_step(self):
        if self.step_cnt != self.step_idx:
            return True
        return False

    def _enqueue_function(self, fn):
        print(f"Enqueuing function call: {fn['id']}")

        # Example message schema
        # queue.send_message({
        #     "function_id": fn["id"],
        #     "workflow_state": self.state
        # })

    def _next(self):
        self.step_cnt += 1
        return self

    def call(self, fn):
        if not self._determine_step():
            return self._next()
        self._update_state(Step(None, "call", fn))
        self._enqueue_function(fn)
        return 

    def done(self):
        return

