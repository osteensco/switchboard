# from dataclasses import dataclass


# @dataclass
# class Registry:
#     def __init__(self) -> None:
#         self.function string
class Step:
    def __init__(self, name, fn) -> None:
        self.name = name
        self.fn = fn

class Workflow:
    def __init__(self, db, context) -> None:
        self.step_idx = 0
        self.step_cnt = 0
        self.context = self._get_context(context)
        self.state = self._init_state(db,)
        self.run_id = self._get_run_id(self.state)
        self.steps = self.state["steps"]

        # workflow is stepped through by tracking the index (number of steps completed) and current count (current index in steps)
        # TODO
        #   - setup caching for conditionals, loops, etc

        # read in context and state
        # create new run_id if we don't have one
        # populate known steps based on the state
        # determine step_idx based on len of known steps
        # for any public method call, we need to determine if that step has been executed based on step idx vs cnt comparison
        # if it hasn't been executed, we push to the queue
        # if we are on the most recently identified step, we need to check if it was successful

    def _get_context(self, context):
        if not context.run_id:
            # generate run_id
            pass

    def _init_state(self, db):
        state = []
        # read state from db
        self.step_idx = len(state)-1
        return {}

    def _update_state(self, step):
        self.step_idx += 1
        self.state[step.name] = step.fn
    
    def _update_db(self, db):
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
        self._update_state(Step("call", fn))
        # push to queue
        return 

    def done(self):
        pass

