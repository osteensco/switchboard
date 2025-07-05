import json
from dataclasses import dataclass
from typing import Callable

from switchboard.schemas import Context

from .db import DBInterface
from .enums import Cloud
from .invocation import Invoke, discover_invocation_endpoint



@dataclass
class ResponseBody():
    ids: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict 

def to_dict(self):
    return self.__dict__


class Response():
    '''
    Response interface for updating the switchboard of the status of a separate component. 
    This could be a task worker or another internal switchboard component.
    '''
    def __init__(
            self, 
            cloud: Cloud,
            db: DBInterface,
            name: str, # Workflow name
            context: Context,
            custom_queue_push: Callable | None = None,
    ) -> None:

        assert len(Context.ids)==3, "ids should be a list of length three representing [run_id, step_id, task_id], if there is no task_id use '-1'"
        self._cloud = cloud
        self._context = context
        self._custom = custom_queue_push
        self._endpoint = discover_invocation_endpoint(db, name)
   
    def _create_default_body(self) -> dict:
        return self._context.to_dict()

    def add_body(self, added_context: dict={}):
        '''
        add_body() must be explicitly called in order to create a response body. 
        By default the body will contain the ids and statuses passed in to the Response obect on initialization.
        Any added context will be placed in the 'cache' field. The 'cache' field is accessible in your workflow as well as any tasks provided to the executor.
        '''
        self.body = self._create_default_body() | {"cache": added_context}

    def send(self):
        '''
        The response object returned here varies by cloud platform.

        AWS - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message.html
        '''
        assert hasattr(self, 'body'), "Must call add_body() method on Response object prior to calling send()."
        body = json.dumps(self.body)
        response = Invoke(self._cloud, self._endpoint, body, self._custom)

        return response



class Trigger(Response):
    '''
    The Trigger object is used to initiate a workflow. This inherits from the `Response` class, and will push a message to the invocation queue that indicates a new run should be started.
    '''
    def __init__(self, cloud: Cloud, db: DBInterface, name: str, custom_queue_push: Callable | None = None) -> None:
        super().__init__(cloud, db, name, Context([-1,-1,-1],True,True,True,{}), custom_queue_push=custom_queue_push)





