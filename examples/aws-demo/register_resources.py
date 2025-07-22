import boto3
import json


with open("./terraform/output.json") as f:
    tf_output = json.load(f)


workflow_name = tf_output["workflow_name"]["value"]
resources_table = tf_output["resources_table_name"]["value"]
executor_queue = tf_output["executor_queue_url"]["value"]
invocation_queue = tf_output["invocation_queue_url"]["value"]

db = boto3.client("dynamodb")

items = [
    {
        "component": {"S": "ExecutorQueue"},
        "name": {"S": workflow_name},
        "url": {"S": executor_queue}
    },
    {
        "component": {"S": "InvocationQueue"},
        "name": {"S": workflow_name},
        "url": {"S": invocation_queue}
    }
]

for i in items:
    resp = db.put_item(
        TableName=resources_table,
        Item=i
    )
    print(f"Added {i} to table {resources_table}.")
