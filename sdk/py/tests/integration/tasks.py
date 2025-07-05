import json
from switchboard.schemas import Cloud
from switchboard.schemas import Task
from switchboard.response import Response
from .db import DBMockInterface
from switchboard.db import DB

db = DB(Cloud.CUSTOM, DBMockInterface(None))
def mockQueue():
    pass

def my_task(context):

    print("Executing my_task (task 1)")

    sb_response = Response(
            Cloud.CUSTOM, 
            db.interface, 
            "my_task", 
            context,
            custom_queue_push=mockQueue
    )
    sb_response.add_body()
    sb_response.send()

    return 200

def my_other_task(context):
    
    print("Executing my_other_task (task 2)")

    sb_response = Response(
            Cloud.CUSTOM, 
            db.interface, 
            "my_task", 
            context,
            custom_queue_push=mockQueue
    )
    sb_response.add_body()
    sb_response.send()

    return 200

def final_task(context):
    
    print("Executing my_task (task 3)")

    sb_response = Response(
            Cloud.CUSTOM, 
            db.interface, 
            "my_task", 
            context,
            custom_queue_push=mockQueue
    )
    sb_response.add_body()
    sb_response.send()

    return 200



directory_map = {
    "my_task": Task(name="my_task", execute=my_task),
    "my_other_task": Task(name="my_other_task", execute=my_other_task),
    "final_task": Task(name="final_task", execute=final_task)
}


