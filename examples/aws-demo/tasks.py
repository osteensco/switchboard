from switchboard.schemas import Task

def hello_world():
    print("Hello from the task!")
    return 200

directory_map = {
    "hello_world_task": Task(name="hello_world_task", execute=hello_world),
}
