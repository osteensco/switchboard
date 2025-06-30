from switchboard.schemas import Task

def my_task():
    print("Executing my_task")
    return 200

directory_map = {
    "my_task": Task(name="my_task", execute=my_task)
}


