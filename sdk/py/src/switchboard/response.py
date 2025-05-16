from typing import Callable
from .enums import Cloud
from .invocation import Invoke
import json


# TODO
#   The response will be used to push a message to the invocation queue
#   This means it needs to be able to discover the required information to publish such a message



class Response():
    '''
    Response interface for updating the switchboard of execution, completion, and success status of a worker.
    '''
    def __init__(self, endpoint: str, cloud: Cloud, custom_queue_push: Callable | None = None) -> None:
        self._cloud = cloud
        self._custom = custom_queue_push
        self._endpoint = endpoint
    
    def build(self, dict: dict={}):
        self._body = self._create_default_body() | dict

    def send(self):
        assert hasattr(self, 'body'), "Must call build() method on Response object prior to calling send()."
        body = json.dumps(self._body)
        response = Invoke(self._cloud, self._endpoint, body, self._custom)

        return response

    def _create_default_body(self) -> dict:
        '''
        Create a dictionary containing necessary fields
        '''
        return {
                # TODO 
                #   Define invocation message schema here or elsewhere
                }






