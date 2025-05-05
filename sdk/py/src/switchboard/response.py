from .enums import Cloud
from .queue import SendMessage


# TODO
#   The response will be used to push a message to the invocation queue
#   This means it needs to be able to discover the required information to publish such a message



class Response():
    '''
    Response interface for updating the switchboard of execution, completion, and success status of a worker.
    '''
    def __init__(self, cloud: Cloud) -> None:
        self.cloud = cloud
        self.body = self._generate_response()
        response = SendMessage(self.body, self.cloud)
        # TODO
        #   this should return a response from the message queue


    def _generate_response(self) -> str:
        '''
        Create a json string containing necessary fields
        '''
        return "{}"



