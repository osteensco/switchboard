import json
from switchboard import InitWorkflow, Call, ParallelCall, Done, DB, Cloud, GetCache

# This is the entry point for your workflow orchestration.
# The `workflow_handler` is invoked by the cloud provider (e.g., AWS Lambda)
# with the context from the invocation queue.
def workflow_handler(event, context):
    """
    Orchestrates the workflow by defining a series of steps.

    This function initializes the Switchboard workflow, retrieves the current
    state and cache, and then defines the sequence of tasks to be executed
    using `Call` and `ParallelCall`. Conditional logic can be implemented
    by checking values in the cache.

    The final step in the handler should always be `Done()` to mark the
    workflow's completion.
    """
    # The event from the invocation queue (e.g., SQS) contains the
    # Switchboard context in the message body.
    # For AWS SQS, the context is in event['Records'][0]['body']
    # You may need to adjust this depending on your trigger source.
    sb_context = event['Records'][0]['body']

    # Initialize the database connection for the appropriate cloud.
    db = DB(Cloud.AWS)

    # Initialize the workflow with the trigger context.
    # This loads the state for the current run or creates a new one.
    InitWorkflow(
        cloud=Cloud.AWS,
        name="my_workflow",  # <-- TODO: Rename your workflow
        db=db,
        context=sb_context
    )

    # Get the cache to use data from previous steps.
    cache = GetCache()

    # --- Define your workflow orchestration below ---

    # Example: Execute a single task and wait for it to complete.
    Call("my_first_step", "sample_task")

    # Example: Execute multiple tasks in parallel.
    # ParallelCall("my_parallel_step", "task_a", "task_b")

    # Example: Use the cache for conditional logic.
    # if cache.get("some_key") == "some_value":
    #     Call("my_conditional_step", "conditional_task")

    # --- End of workflow definition ---

    # Mark the workflow as complete.
    return Done()
