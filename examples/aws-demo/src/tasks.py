from switchboard import Task, Response, Cloud, DB, Context

# This is a sample task. You can define your own tasks in this file.
def sample_task(context: Context):
    # initialize the db connection
    db = DB(Cloud.AWS)
    
    # do some work
    print(f"This is a sample task. context - {context}")
    
    # update the context
    context.success = True 
    context.completed = True
    
    # create a response object
    sb_response = Response(
            Cloud.AWS, 
            db.interface, 
            "myworkflow", 
            context
    )

    # send the response to the invocation queue to update the workflow
    sb_response.send()
    return 200

# The task_map maps task names to Task objects.
# The executor will use this map to find and execute your tasks.
task_map = {
    "sample_task": Task(name="sample_task", execute=sample_task),
}

