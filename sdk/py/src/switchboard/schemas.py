from dataclasses import dataclass





@dataclass
class Registry:
    # TODO 
    #   hammer out details of the schema
    #   probably need a class for what will ultimately be the 'fn' argument in the Workflow methods
    #       what information would be needed to run each type of execution?
    #       should a trigger map to specific executions?
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

    def to_dict(self):
        return {
                "run_id": self.run_id,
                "steps": self.steps,
                "cache": self.cache
                }


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



