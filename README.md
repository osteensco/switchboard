<div align="center">
    
```
◌  ◌  ● 
◌  ●  ◌ 
◌  ●  ◌ 
●  ◌  ◌ 

s w i t c h b o a r d

```

</div>


# Switchboard

**Event-driven, serverless orchestration-as-code.**

Switchboard is a lightweight, event-driven, and serverless state machine that provides glue-as-a-service. It allows you to define and orchestrate complex workflows across cloud services using simple, declarative code in your preferred language.

## What is Switchboard?

At its core, Switchboard is designed to solve the "glue" problem in modern serverless architectures. Instead of relying on complex, hard-to-manage infrastructure or proprietary platform services, Switchboard empowers you to define your orchestration logic as code. This makes your workflows more transparent, version-controllable, and easier to debug.

It's built to be cloud-agnostic and abstracts away the complexities of long-running jobs, state management, and inter-service communication in a serverless world.

## Key Features

*   **Orchestration-as-Code:** Define your workflows directly in Python (and soon other languages). No complex YAML or JSON configurations.
*   **Cloud-Agnostic by Design:** While the initial implementation focuses on AWS (using DynamoDB and SQS), the architecture is designed with pluggable interfaces for other cloud providers like GCP and Azure.
*   **Handles Long-Running Jobs:** Switchboard seamlessly manages the state of long-running tasks without requiring you to build complex polling or callback mechanisms.
*   **Cost-Effective:** By leveraging pay-per-use serverless functions and message queues, Switchboard can be a significantly cheaper orchestration solution compared to traditional, always-on workflow engines.
*   **Multi-Language Support:** A Python SDK is currently available. Go and TypeScript SDKs are under development.
*   **Fully Open Source:** Switchboard is fully open-sourced and community-driven.

## How it Works

Switchboard's architecture is simple and robust, relying on standard cloud primitives.

1.  **Workflow:** A serverless function that runs your workflow definition code.
2.  **State Database:** A key-value store (like DynamoDB) that persists the state of every workflow run.
3.  **Message Queues:** Used to reliably trigger task executors and receive their responses.
4.  **Executor:** A serverless function that executes or triggers execution of your individual tasks (your business logic).

A typical workflow execution looks like this:
`Trigger -> Invocation Queue -> Workflow -> Executor -> Response -> Invocation Queue`

## Getting Started (Python Example)

Here’s a conceptual look at how you would define a workflow with the Python SDK.

### 1. Define your tasks

Create a `tasks.py` file that maps task names to functions. These are your units of work.

```python
# tasks.py

from switchboard.schemas import Task

def process_data():
    # Your business logic here
    print("Processing some data...")
    return 200

def generate_report():
    # Your business logic here
    print("Generating report...")
    return 200

def another_task():
    # Your business logic here
    print("task complete!")
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

from switchboard import InitWorkflow, Call, ParallelCall, Done, DB, Cloud

def workflow_handler(context):
    # Initialize the database connection
    db = DB(Cloud.AWS)

    # Initialize the workflow with the trigger context
    InitWorkflow(
        cloud=Cloud.AWS,
        name="my_first_workflow",
        db=db,
        context=context
    )

    # Execute a single task and wait for it to complete
    Call("process_data_task")

    # Execute multiple tasks in parallel
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
*   **CLI Tool:** For easy setup, management, and deployment of Switchboard resources.
*   **Go & TypeScript SDKs:** Bringing multi-language support to more developers.
*   **Enhanced Observability:** Integrating logging, monitoring, and tracing.
*   **Advanced Configuration:** Get as far into the weeds as you see fit.
*   **Comprehensive Documentation & Examples.**

## Contributing

Contributions are welcome!

## License

This project is licensed under the Apache 2.0 License.
