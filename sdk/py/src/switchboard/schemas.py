from dataclasses import dataclass
from typing import Callable

from .enums import (
    Cloud, 
    CloudResource, 
    CloudResourceType,
    Status, 
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
    step_name: str # used to identify if step has already been called in _determine_step_execution
    task_key: str # key that will be used to lookup function in task_map in executor function's tasks.py
    executed: bool = False
    completed: bool = False
    success: bool = False
    task_id: int = -1 # -1 unless step is part of a tasks list in a parallel step
    retries: int = 0

    def to_dict(self):
        return self.__dict__


@dataclass
class ParallelStep:
    step_id: int
    step_name: str # used to identify if step has already been called in _determine_step_execution
    tasks: list[Step] 
    executed: bool = False
    completed: bool = False
    success: bool = False

    def to_dict(self):
        tasks = [task.to_dict() for task in self.tasks]
        d = self.__dict__
        d["tasks"] = tasks
        return d


# dataclass for SwitchboardState table
@dataclass
class State:
    name: str
    run_id: int
    steps: list[Step|ParallelStep]
    cache: dict # cache can be used to store data that is pertinent to conditional steps in a workflow.
    status: Status

    def to_dict(self):
        steps = [step.to_dict() for step in self.steps]
        d = self.__dict__
        d["steps"] = steps
        return d


def NewState(data: dict) -> State:
    '''
    Takes the state as a dictionary and converts to a State object.
    '''
    deserialized_steps = []
    for step_data in data["steps"]:
        if "tasks" in step_data: # It's a ParallelStep
            deserialized_tasks = [Step(**task_data) for task_data in step_data["tasks"]]
            deserialized_steps.append(ParallelStep(**{**step_data, "tasks": deserialized_tasks}))
        else: # It's a Step
            deserialized_steps.append(Step(**step_data))
    return State(data["name"], int(data["run_id"]), deserialized_steps, data["cache"], data["status"])




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
    workflow: str
    ids: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict # cache is used to add variables to the State cache which can be defined in the switchboard response object body.

    def to_dict(self):
        d = self.__dict__
        d["ids"] = [int(i) for i in d["ids"]]
        return d



# dataclass for SwitchboardResources table
@dataclass
class Resource:
    component: SwitchboardComponent
    url: str
    cloud: Cloud
    resource: CloudResource
    resource_type: CloudResourceType



