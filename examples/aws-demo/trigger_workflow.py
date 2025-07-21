import boto3
import json
import time
import uuid

def get_terraform_outputs():
    """Reads the Terraform outputs from the state file."""
    try:
        with open("terraform/terraform.tfstate") as f:
            state = json.load(f)
        return state["outputs"]
    except FileNotFoundError:
        print("Error: terraform.tfstate not found. Please run `terraform apply` first.")
        exit(1)

def trigger_workflow(invocation_queue_url):
    """Sends a message to the invocation queue to trigger the workflow."""
    sqs = boto3.client("sqs", region_name="us-east-1") # Ensure region is correct
    message_body = {
        "ids": [-1, -1, -1], # Signal to workflow to generate new run_id
        "executed": True,
        "completed": True,
        "success": True,
        "cache": {},
        "workflow": "my_workflow",
        "execute": ""
    }
    sqs.send_message(
        QueueUrl=invocation_queue_url,
        MessageBody=json.dumps(message_body)
    )
    print(f"Successfully triggered workflow.")

from boto3.dynamodb.conditions import Key

def monitor_workflow(state_table_name, workflow_name):
    """Monitors the workflow by polling the DynamoDB state table."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1") # Ensure region is correct
    table = dynamodb.Table(state_table_name)
    
    print("\n--- Workflow Execution ---")
    
    # Wait for the workflow to be initiated and get its run_id
    run_id = None
    start_time = time.time()
    while time.time() - start_time < 60: # Wait up to 60 seconds for initial entry
        response = table.query(
            KeyConditionExpression=Key('name').eq(workflow_name),
            ScanIndexForward=False, # Get the latest run_id
            Limit=1
        )
        items = response.get('Items', [])
        if items:
            run_id = int(items[0]['run_id']) # Ensure run_id is an integer
            print(f"Found workflow with run_id: {run_id}")
            break
        print("Waiting for workflow to be initiated in DynamoDB...")
        time.sleep(5)
    
    if run_id is None:
        print("Error: Workflow not initiated in DynamoDB within timeout.")
        return

    start_time = time.time()
    while time.time() - start_time < 120:  # 2-minute timeout for monitoring
        try:
            response = table.get_item(
                Key={"name": workflow_name, "run_id": run_id}
            )
            item = response.get("Item")
            if item:
                print(f"  Status: {item.get('status')}, Current Step: {item.get('current_step')}")
                if item.get('status') == 'COMPLETED' or item.get('status') == 'FAILED':
                    print("--- Workflow Finished ---")
                    break
            else:
                print("  Workflow initiated, waiting for status updates...")

        except Exception as e:
            print(f"An error occurred: {e}")
            break
        
        time.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    outputs = get_terraform_outputs()
    invocation_queue_url = outputs["invocation_queue_url"]["value"]
    state_table_name = outputs["state_table_name"]["value"]
    
    trigger_workflow(invocation_queue_url)
    monitor_workflow(state_table_name, "my_workflow") # Pass workflow_name to monitor
