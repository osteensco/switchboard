<div  align=center>
<img width="181" height="159" alt="image" src="https://github.com/user-attachments/assets/ffc35ecd-959e-4cf1-a226-6725d13b7376" />
<div align=center>
    <h1>Switchboard</h1>
    <b>Event-driven, serverless orchestration-as-code.</b></div>
</div>







## What is Switchboard?

Switchboard is a serverless orchestration and durable-execution framework that turns native cloud primitives into a workflow runtime. 
Write workflows as ordinary code, deploy them into your existing cloud environment, and get durable state, retries, parallelism, observability, and long-running execution without operating a seperate orchestration service.
Switchboard is built to be cloud-agnostic and provides managed-orchestration ergonomics without a dedicated orchestration service. Switchboard achieves this by leveraging existing cloud primitives, making it ideal for teams already heavily invested in serverless cloud infrastructure.

 - **Glue-as-A-Service** -
    Writing glue code manually for every workflow is repetitive, error-prone, and complex. It forces you to focus on infrastructure plumbing instead of business logic.
    Switchboard provides a structured framework and SDK that abstracts away this complexity into reusable, pre-fabricated orchestration infrastructure.

 - **Orchestration-as-Code** - 
    Switchboard lets you define orchestration logic as ordinary application code rather than through a proprietary workflow language or external configuration. 
    This keeps workflow behavior transparent, testable, easier to develop and debug, and versioned alongside the application itself.

 - **Durable Execution** - 
    Switchboard persists workflow progress so execution can survive failures, retries, process termination, and long-running waits. 
    This durability extends across individual tasks and services within the same workflow, allowing execution to safely resume without rebuilding state or manually coordinating retries and idempotency.


## Key Features

*   **Native Cloud Runtime:** Switchboard uses standard cloud primitives such as serverless functions, message queues, databases, and logging services as the underlying workflow runtime. No dedicated orchestration service is required.
*   **Durable Execution:** Persist workflow progress across task execution, failures, retries, process termination, and long-running waits.
*   **Orchestration-as-Code:** Define workflows using ordinary application code rather than YAML, JSON, or a proprietary workflow definition language.
*   **Prefabricated Infrastructure:** Deploy the infrastructure required for orchestration using reusable templates with sound defaults, while retaining the ability to customize the underlying cloud resources.
*   **Long-Running Workflows:** Coordinate work that spans seconds, hours, or longer without keeping compute continuously running or building custom polling and callback infrastructure.
*   **Cloud-Agnostic Architecture:** Switchboard uses pluggable cloud interfaces so the same execution model can be implemented using the native primitives of different cloud providers.
*   **Integrated Developer Tooling:** Switchboard's CLI is designed to provide a single interface for deploying workflows, inspecting executions, viewing logs, managing resources, and troubleshooting failures.
*   Multi-Language SDKs: Python is currently supported, with Go and TypeScript SDKs planned.
*   **Open Source:** Switchboard is fully open source under the Apache 2.0 License.

## How it Works

Switchboard builds a durable workflow runtime from standard cloud primitives. A deployment consists of four primary components:

1. **Workflow:** A serverless function containing your orchestration logic. Workflow execution is replayable and progresses from persisted state rather than relying on a continuously running process.
2. **State Store:** Persists workflow execution state, task status, intermediate data, and metadata required to resume and inspect workflow runs.
3. **Message Queues:** Reliably decouple workflow execution from task execution and carry invocations and responses between components.
4. **Executor:** Dispatches individual units of work. Tasks can execute directly within the executor or invoke external services while Switchboard coordinates their completion.

A typical workflow execution looks like this:

```
Trigger ─► Invocation Queue ◄─┐
                 ▼            |
              Workflow        |
                 ▼            |
           Executor Queue     |
                 ▼            |
              Executor        |
                 ▼            |
               Task           |            
                 ▼            |
             Response ────────┘
```

Each response advances the persisted workflow state and re-invokes the workflow, allowing execution to continue without keeping the orchestrator continuously running.

## Getting Started (Python Example)

Here’s a conceptual look at how you would define a workflow with the Python SDK (requires Python3.11+).

### 1. Define your tasks

Create a `tasks.py` file that maps task names to functions. These are your units of work.

```python
# tasks.py

from switchboard import Task, Response, Cloud, Context

# In order to update the workflow state
# Wherever you place your business logic,
# You will need to update the context and send a response
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

task_map = {
    "process_data_task": Task(name="process_data_task", execute=process_data),
    "generate_report_task": Task(name="generate_report_task", execute=generate_report),
    "another_task": Task(name="another_task", execute=another_task),
}
```

**NOTE**: Tasks may execute directly within the executor or dispatch work to external services. 
For synchronous tasks, completion can be observed directly. For asynchronously dispatched work, the executing service sends a response back to Switchboard when the work is complete. 
This allows workflows to coordinate distributed services without treating message delivery as task completion.

### 2. Define your workflow

In your main handler, define the orchestration logic using the Switchboard SDK.

```python
# main.py (your orchestrator's handler)

from switchboard import InitWorkflow, Call, ParallelCall, Done, DB, Cloud, GetCache

def workflow_handler(context):
    # Initialize the database connection
    db = DB(Cloud.AWS)

    # Initialize the workflow with the context
    InitWorkflow(
        cloud=Cloud.AWS,
        name="my_first_workflow",
        db=db,
        context=context
    )

    # Execute a single task and wait for it to complete, optionally define number of retries
    Call("process_data_task", retries=3)
    
    # Retrieve data passed between workflow steps or from executed tasks
    data = GetCache()

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
    * [ ] Commands (see TODO in cli dir)
    * [ ] Rich and interactive TUI
* [ ]   **SDKs:** Bringing multi-language support to more developers.
    * [x] Python
    * [ ] Golang
    * [ ] TypeScript
* [ ]   **Enhanced Observability:** Integrating logging, monitoring, and tracing.
    * [ ] Out-of-the-box default log sink
    * [ ] View and query logs through CLI tool
* [x]   **Advanced Configuration:** Get as far into the weeds as you see fit.
    * [x] Accessible templates with sound defaults
* [ ]   **Comprehensive Documentation & Examples.**
    * [x] AWS demo with python
    * [x] Quickstart command in CLI
    * [ ] Docs (markdown files in repo)
        * [x] Admin
        * [ ] Quickstart guide
        * [ ] SDK docs
        * [ ] CLI Tool user manual

## Contributing

Contributions are welcome! Please first raise an issue or reference specific issues in your PR.

## License

This project is licensed under the Apache 2.0 License.

## Project diagrams and other notes
![image](https://github.com/user-attachments/assets/632e95d7-03ca-4203-9b22-4ebca6614ff3) 
![image](https://github.com/user-attachments/assets/d2c44162-eb2e-4ffa-9b77-9b7870246b80)

