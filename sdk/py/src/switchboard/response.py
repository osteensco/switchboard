from dataclasses import dataclass
from typing import Callable
from .enums import Cloud
from .invocation import Invoke, discover_invocation_endpoint
import json


# TODO
#   The response will be used to push a message to the invocation queue
#   This means it needs to be able to discover the required information to publish such a message
#       Only the URL would be needed as IAM roles should take care of permissions, which means it can be discoverable in the database

@dataclass
class ResponseBody():
    ids: list[int]
    executed: bool
    completed: bool
    success: bool
    cache: dict 


class Response():
    '''
    Response interface for updating the switchboard of execution, completion, and success status of a worker.
    '''
    def __init__(
            self, 
            cloud: Cloud, 
            name: str, 
            ids: list[int], 
            status: list[bool]=[True,True,True], 
            custom_queue_push: Callable | None = None,
    ) -> None:

        assert len(ids)==3, "ids should be a list of length three representing [run_id, step_id, task_id]"
        assert len(status)==3, "status should be a list of length three representing [executed, completed, success]"
        self._cloud = cloud
        self._ids = ids
        self._status = status
        self._custom = custom_queue_push
        self._endpoint = discover_invocation_endpoint(cloud, name)
   
    def _create_default_body(self) -> dict:
        return {
            "ids": self._ids,
            "executed": self._status[0],
            "completed": self._status[1],
            "success":self._status[2] 
        }


    def add_body(self, added_context: dict={}):
        '''
        add_body() must be explicitly called in order to create a response body. 
        By default the body will contain the ids and statuses passed in to the Response obect on initialization.
        If you are maintainig a cache field for your switchboard's context, this field must be included in the added_context argument.
        '''
        self.body = self._create_default_body() | added_context

    def send(self):
        assert hasattr(self, 'body'), "Must call add_body() method on Response object prior to calling send()."
        body = json.dumps(self.body)
        response = Invoke(self._cloud, self._endpoint, body, self._custom)

        return response







