import json
from dataclasses import dataclass
from typing import Callable

from switchboard.logging_config import log
from switchboard.schemas import Context

from .db import DBInterface
from .enums import Cloud
from .invocation import QueuePush, discover_invocation_endpoint



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

        log.bind(
            component="Response",
            workflow_name=name,
            context=context,
        ).info("-- Response object created. --")

        assert len(context.ids)==3, "ids should be a list of length three representing [run_id, step_id, task_id], if there is no task_id use '-1'"
        self._cloud = cloud
        self._context = context
        self._custom = custom_queue_push
        self._endpoint = discover_invocation_endpoint(db, name)
        self.body = self._context.to_dict()

    def send(self):
        '''
        The response object returned here varies by cloud platform.

        AWS - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message.html
        '''
        body = json.dumps(self.body)
        response = QueuePush(self._cloud, self._endpoint, body, self._custom)

        return response



class Trigger(Response):
    '''
    The Trigger object is used to initiate a workflow. This inherits from the `Response` class, and will push a message to the invocation queue that indicates a new run should be started.
    '''
    def __init__(self, cloud: Cloud, db: DBInterface, name: str, custom_queue_push: Callable | None = None) -> None:
        super().__init__(cloud, db, name, Context(name, [-1,-1,-1],True,True,True,{}), custom_queue_push=custom_queue_push)
        self.send()





