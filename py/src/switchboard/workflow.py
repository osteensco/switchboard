import json
from dataclasses import dataclass
from typing import Callable





@dataclass
class Registry:
    # TODO 
    #   hammer out details of the schema
    contacts: dict


@dataclass
class Step:
    run_id: list[int]
    name: str
    fn: Callable
    success: bool = False


@dataclass
class State:
    steps: list[Step]
    run_id: int


@dataclass
class Context:
    run_id: list[int]
    success: bool


# context = {
#             "run_id": [
#                 100, # workflow id
#                 1 # worker id
#             ],
#             "success" : True,
#             ...some other fields maybe...
#         }


class Workflow:
    def __init__(self, db, context) -> None:
        
        self.step_idx = 0
        self.step_cnt = 0

        self.db = db
        self.context = self._get_context(context)
        
        self.state = self._init_state(db)


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
        # context should provide last worker success status, workflow run_id and worker run_id
        # verify run_id is not marked as complete (this should never occur but an important assertion to make)

    def _get_context(self, context) -> Context:
        raw = json.loads(context) 
        try:
            cntx = Context(raw["run_id"], raw["success"])
        except: # newly triggered workflows wont have a run_id or success field
            cntx = Context(self._generate_id(), False)

        if cntx.run_id[0] == 0:
            return cntx

        return cntx
        

    def _init_state(self, db) -> State:
        # read state from db with run_id
        state = db.read(self.context.run_id[0])
        if not state:
            # handle new state creation (new workflow run)
            state = State([], self.context.run_id[0])
        if self.context.success:
            state.steps[-1].success = True
        else:
            pass
            # apply retry logic
            # retry logic should have a default and be defined by the user
        self.step_idx = len(state.steps)-1
        return state

    def _update_state(self, step):
        self.step_idx += 1
        self.state.steps.append(step)
    
    def _update_db(self, db):
        # write self.state to db using self.state.run_id
        db.write(self.state.run_id, self.state)
        

    def _generate_id(self) -> list[int]:
        # TODO
        #   implement
        return [0,0]

    def _generate_worker_id(self):
        return self.context.run_id[1]+1

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
        self._update_db(self.db)
        if not self._determine_step():
            return self._next()
        self._update_state(Step([self.state.run_id, self._generate_worker_id()], "call", fn))
        self._enqueue_function(fn)
        return 

    def done(self):
        return

