import json
from switchboard.schemas import Cloud, Context, ContextFromDict
from switchboard.schemas import Task
from switchboard.response import Response
from .db import DBMockInterface
from switchboard.db import DB







db = DB(Cloud.CUSTOM, DBMockInterface(None))

# This class provides an interface in which tests can use to properly set their custom queue push functions for each task
class InvocationQueue:
    def __init__(self):
        self._push_func = None

    def set_push_function(self, func):
        self._push_func = func

    def push(self, body):
        if self._push_func:
            self._push_func(body)
        else:
            print(f"InvocationQueue: No push function set. Body: {body}")

mock_invocation_queue = InvocationQueue()



def generic_response(context: Context):
    context.success = True
    context.completed = True
    sb_response = Response(
            Cloud.CUSTOM, 
            db.interface, 
            "my_workflow", 
            context,
            custom_queue_push=mock_invocation_queue.push
    )
    # sb_response.add_body()
    sb_response.send()

    return 200



def my_task(context: Context):
    print("!!!!!! - Executing my_task (task 1)")
    return generic_response(context)

def my_other_task(context: Context):
    print("!!!!!! - Executing my_other_task (task 2)")
    return generic_response(context)

def final_task(context: Context):
    print("!!!!!! - Executing final_task (task 3)")
    return generic_response(context)

# first set of parallel tasks
def psyyych(context: Context):
    print("!!!!!! - Executing psyyych (parallel task)")
    return generic_response(context)

def anotherone(context: Context):
    print("!!!!!! - Executing anotherone (parallel task)")
    return generic_response(context)

def yetanother(context: Context):
    cntxt = context
    cntxt.cache['test_true'] = True

    print("!!!!!! - Executing yetanother (parallel task)")
    return generic_response(cntxt)


# second set of parallel tasks
def conditional1(context: Context):
    context.cache['test_false'] = False
    print("!!!!!! - Executing conditional1 (parallel task)")
    return generic_response(context)

def conditional2(context: Context):
    print("!!!!!! - Executing conditional2 (parallel task)")
    return generic_response(context)

# these shouldn't run
def badstep1(context: Context):
    print("!!!!!! - I SHOULDNT RUN NOOOOOO (badstep1)")
    return generic_response(context)

def badstep2(context: Context):
    print("!!!!!! - I SHOULDNT RUN NOOOOOO (badstep2)")
    return generic_response(context)


# actual final task
def endstep(context: Context):
    print("!!!!!! - This is the last executed task")
    return generic_response(context)














directory_map = {
    "my_task": Task(name="my_task", execute=my_task),
    "my_other_task": Task(name="my_other_task", execute=my_other_task),
    "final_task": Task(name="final_task", execute=final_task),
    "psyyych": Task("psyyych",psyyych),
    "anotherone": Task("anotherone",anotherone),
    "yetanother": Task("yetanother",yetanother),
    "conditional1": Task("conditional1",conditional1),
    "conditional2": Task("conditional2",conditional2),
    "badstep1": Task("badstep1",badstep1),
    "badstep2": Task("badstep2",badstep2),
    "endstep": Task("endstep", endstep)
}




