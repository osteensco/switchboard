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
        self.cloud = cloud
        self.custom = custom_queue_push
        self.body = self._generate_response()
        self.endpoint = endpoint

    def send(self):
        body = json.dumps(self.body)
        response = Invoke(self.cloud, self.endpoint, body, self.custom)
        # TODO
        #   this should return a response from the message queue
        assert response
        return response

    def _generate_response(self) -> dict:
        '''
        Create a json string containing necessary fields
        '''
        return {
                # TODO 
                #   Define invocation message schema here or elsewhere
                }






