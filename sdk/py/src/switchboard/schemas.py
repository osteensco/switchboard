from dataclasses import dataclass
from typing import Callable

from .enums import (
    Cloud, 
    CloudResource, 
    CloudResourceType, 
    SwitchboardComponent
)




# task object for tasks.py
@dataclass
class Task:
    name: str
    execute: Callable


@dataclass
class Step:
    step_id: int
    task_key: str # key that will be used to lookup function in directory_map in executor function's tasks.py
    executed: bool = False
    completed: bool = False
    success: bool = False
    task_id: int = -1
    retries: int = 0


@dataclass
class ParallelStep:
    step_id: int
    tasks: list[Step] 
    executed: bool = False
    completed: bool = False
    success: bool = False


@dataclass
class State:
    name: str
    run_id: int
    steps: list[Step|ParallelStep]
    cache: dict # cache can be used to store data that is pertinent to conditional steps in a workflow.

def NewState(dict) -> State:
    return State(dict["name"], dict["run_id"], dict["steps"], dict["cache"])


# context = {
#             "ids": [
#                 100, # run id
#                 1 # step id
#                 -1 # task id
#             ],
#             "success" : True,
#             ...etc...
#         }
@dataclass
class Context:
    '''
    ids - [
        100, # run id
        1 # step id
        -1 # task id
    ]
    '''
    ids: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict # cache is used to add variables to the State cache which can be defined in the switchboard response object body.

    def to_dict(self):
        return {
                "ids": self.ids,
                "executed": self.executed,
                "completed": self.completed,
                "success": self.success,
                "cache": self.cache,
                }


# dataclass for cloud endpoints.
@dataclass
class Endpoint:
    component: SwitchboardComponent
    url: str
    cloud: Cloud
    resource: CloudResource
    resource_type: CloudResourceType



