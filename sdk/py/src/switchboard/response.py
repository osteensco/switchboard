from typing import Callable
from .enums import Cloud
from .invocation import Invoke


# TODO
#   The response will be used to push a message to the invocation queue
#   This means it needs to be able to discover the required information to publish such a message



class Response():
    '''
    Response interface for updating the switchboard of execution, completion, and success status of a worker.
    '''
    def __init__(self, cloud: Cloud, custom_queue_push: Callable | None = None) -> None:
        self.cloud = cloud
        self.body = self._generate_response()
        response = Invoke(self.cloud, self.body, custom_queue_push)
        # TODO
        #   this should return a response from the message queue


    def _generate_response(self) -> str:
        '''
        Create a json string containing necessary fields
        '''
        return "{}"



