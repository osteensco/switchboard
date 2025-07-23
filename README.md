<div  align=center>
<img width="181" height="159" alt="image" src="https://github.com/user-attachments/assets/ffc35ecd-959e-4cf1-a226-6725d13b7376" />
</div>


# Switchboard

**Event-driven, serverless orchestration-as-code.**

Switchboard is a lightweight, event-driven, and serverless state machine that provides glue-as-a-service. 
It allows you to define and orchestrate complex workflows across microservices using simple, declarative code in your preferred language.

## What is Switchboard?

**Glue-as-A-Service**
    Writing glue code manually for every workflow is repetitive, error-prone, and complex. It forces you to focus on infrastructure plumbing instead of business logic.
    Switchboard provides a structured framework and an SDK that abstracts away this complexity, effectively acting as pre-fabricated, high-quality glue.

**Orchestration-as-Code**
    Instead of relying on complex, hard-to-manage infrastructure or proprietary platform services, Switchboard empowers you to define your orchestration logic as code. 
    This makes your orchestration logic more transparent, faster to develop and deploy, and easier to debug.

Switchboard is built to be cloud-agnostic and provides managed service abstractions without managed service cost.

## Key Features

*   **Orchestration-as-Code:** Define your workflows using your preferred language. No complex YAML or JSON configurations, just logic flow an simple functions from the SDK.
*   **Multi-Language Support:** A Python SDK is currently available. Go and TypeScript SDKs are under development.
*   **Cloud-Agnostic by Design:** The Switchboard architecture is designed with pluggable interfaces for any cloud environment, providing robust defaults while empowering custom implementation if desired.
*   **Handles Long-Running Jobs:** Switchboard seamlessly manages the state of long-running tasks without requiring you to build complex polling or callback mechanisms.
*   **Cost-Effective:** By utilizing serverless functions and message queues, Switchboard can be a significantly cheaper orchestration solution compared to traditional, always-on workflow engines like Airflow.
*   **Fully Open Source:** Switchboard is fully open-sourced and community-driven.

## How it Works

Switchboard's architecture is simple and robust, relying on standard cloud primitives.

1.  **Workflow:** A serverless function that runs your orchestration, defined in code.
2.  **Database:** Persists the state of every workflow run, as well as enabling discoverability of switchboard's components.
3.  **Message Queues:** Enables decoupled componenets to reliably trigger workflows, task executors, and receive their responses.
4.  **Executor:** A serverless function that executes or triggers execution of your individual tasks (your business logic).

A typical workflow execution looks like this:
`Trigger -> Invocation Queue -> Workflow -> Executor Queue -> Executor -> Task -> Response -> Invocation Queue -> State Update and Continue Workflow`

## Getting Started (Python Example)

Here’s a conceptual look at how you would define a workflow with the Python SDK (requires Python3.11+).

### 1. Define your tasks

Create a `tasks.py` file that maps task names to functions. These are your units of work.

```python
# tasks.py

from switchboard import Task, Response, Cloud, Context

# You will need to update the context and send a response wherever you run your business logic in order to update the workflow state
def generic_response(context: Context):
    # initialize the db connection
    db = DB(Cloud.AWS)
    # update the context
    context.success = True 
    context.completed = True
    # create the response object
    sb_response = Response(
            Cloud.AWS, 
            db.interface, 
            "my_first_workflow", 
            context
    )
    # send the response to the invocation queue 
    # this updates the workflow
    sb_response.send()


# for light tasks you can define business logic directly in the task's function.
def process_data(context: Context):
    # Your business logic here
    print("Processing some data...")
    # you can utilize the cache in the context to pass data between workflow components or downstream microservices
    context.cache["some_bool_field"] = True
    generic_response(context)
    return 200

def generate_report(context: Context):
    # Your business logic here
    print("Generating report...")
    generic_response(context)
    return 200

# most use cases will utilize microservices, you can trigger those in your defined tasks
def another_task(context: Context):
    # Call your microservice here
    print("Task triggered!")
    # Your microservice will need to provide a response to the workflow
    return 200

directory_map = {
    "process_data_task": Task(name="process_data_task", execute=process_data),
    "generate_report_task": Task(name="generate_report_task", execute=generate_report),
    "another_task": Task(name="another_task", execute=another_task),
}
```

### 2. Define your workflow

In your main handler, define the orchestration logic using the Switchboard SDK.

```python
# main.py (your orchestrator's handler)

from switchboard import InitWorkflow, Call, ParallelCall, Done, DB, Cloud, GetCache

def workflow_handler(context):
    # Initialize the database connection
    db = DB(Cloud.AWS)

    # Initialize the workflow with thecontext
    InitWorkflow(
        cloud=Cloud.AWS,
        name="my_first_workflow",
        db=db,
        context=context
    )

    # Retrieve data passed between workflow steps or from executed tasks
    data = GetCache()

    # Execute a single task and wait for it to complete
    Call("process_data_task")

    # Conditionally execute multiple tasks in parallel
    if data["some_bool_field"]:
        ParallelCall(
            "generate_report_task",
            "another_task"
        )

    # Mark the workflow as complete
    return Done()
```

## Project Status & Roadmap

Switchboard is currently in active development. The Python SDK is the most mature part of the project.

Roadmap inclues:
* [ ]   **CLI Tool:** For easy setup, management, and deployment of Switchboard resources.
* [-]   **SDKs:** Bringing multi-language support to more developers.
    * [x] Python
    * [ ] Golang
    * [ ] TypeScript
* [ ]   **Enhanced Observability:** Integrating logging, monitoring, and tracing.
    * [ ] Out-of-the-box default log sink
    * [ ] View and query logs through CLI tool
* [ ]   **Advanced Configuration:** Get as far into the weeds as you see fit.
    * [ ] Accessible templates with sound defaults
* [-]   **Comprehensive Documentation & Examples.**
    * [x] AWS demo with python
    * [ ] Quickstart command in CLI
    * [ ] Docs site

## Contributing

Contributions are welcome! Please first raise an issue or reference specific issues in your PR.

## License

This project is licensed under the Apache 2.0 License.

## Project diagrams and other notes
![image](https://github.com/user-attachments/assets/632e95d7-03ca-4203-9b22-4ebca6614ff3) 
![image](https://github.com/user-attachments/assets/d2c44162-eb2e-4ffa-9b77-9b7870246b80)

