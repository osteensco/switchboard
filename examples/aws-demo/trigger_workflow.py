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

def trigger_workflow(invocation_queue_url, run_id):
    """Sends a message to the invocation queue to trigger the workflow."""
    sqs = boto3.client("sqs")
    message_body = {
        "run_id": run_id,
        "workflow_name": "my_workflow",
        # Add any other initial data you want to pass to the workflow
    }
    sqs.send_message(
        QueueUrl=invocation_queue_url,
        MessageBody=json.dumps(message_body)
    )
    print(f"Successfully triggered workflow with run_id: {run_id}")

def monitor_workflow(state_table_name, run_id):
    """Monitors the workflow by polling the DynamoDB state table."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(state_table_name)
    
    print("\n--- Workflow Execution ---")
    
    start_time = time.time()
    while time.time() - start_time < 300:  # 5-minute timeout
        try:
            response = table.get_item(
                Key={"name": "my_workflow", "run_id": run_id}
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
    
    run_id = str(uuid.uuid4())
    
    trigger_workflow(invocation_queue_url, run_id)
    monitor_workflow(state_table_name, run_id)
