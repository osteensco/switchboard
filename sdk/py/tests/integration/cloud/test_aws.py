import os
import pytest
from moto import mock_aws
import boto3
from switchboard.cloud import AWS_db_connect, AWS_message_push
from switchboard.db import AWS_DataInterface
from switchboard.enums import Status, TableName, SwitchboardComponent, Cloud
from switchboard.schemas import State



@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# db.py
@pytest.fixture
def init_resource(aws_credentials):
    with mock_aws():
        yield boto3.resource('dynamodb', region_name='us-east-1')

@pytest.fixture
def dynamodb_resource(init_resource):
    # Create SwitchboardState table
    dynamodb = init_resource
    dynamodb.create_table(
        TableName=TableName.SwitchboardState.value,
        KeySchema=[
            {'AttributeName': 'name', 'KeyType': 'HASH'},
            {'AttributeName': 'run_id', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'name', 'AttributeType': 'S'},
            {'AttributeName': 'run_id', 'AttributeType': 'N'},
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    # Create SwitchboardResources table
    dynamodb.create_table(
        TableName=TableName.SwitchboardResources.value,
        KeySchema=[
            {'AttributeName': 'component', 'KeyType': 'HASH'},
            {'AttributeName': 'name', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'component', 'AttributeType': 'S'},
            {'AttributeName': 'name', 'AttributeType': 'S'},
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    yield dynamodb


@pytest.fixture
def aws_interface(dynamodb_resource):
    return AWS_DataInterface(dynamodb_resource)


def test_write_and_read(aws_interface):
    state_obj = State(name="test_workflow", run_id=1, steps=[], cache={}, status=Status.InProcess)
    aws_interface.write(state_obj)

    result = aws_interface.read("test_workflow", 1)
    assert result
    assert result.name == "test_workflow"
    assert result.run_id == 1
    assert result.status == Status.InProcess

def test_read_returns_none(aws_interface):
    result = aws_interface.read("test_new_workflow",-1)
    assert result is None

def test_increment_id_empty_table(aws_interface):
    new_id = aws_interface.increment_id("workflow_x")
    assert new_id == 1


def test_increment_id_existing(aws_interface):
    # Manually insert one item
    table = aws_interface.get_table()
    table.put_item(Item={"name": "workflow_x", "run_id": 7})
    
    new_id = aws_interface.increment_id("workflow_x")
    assert new_id == 8


def test_get_endpoint_success(aws_interface):
    tbl = aws_interface.get_table(TableName.SwitchboardResources)
    tbl.put_item(Item={
        "component": SwitchboardComponent.ExecutorQueue.value,
        "name": "test_workflow",
        "url": "https://sqs/mock/url",
        "cloud": Cloud.AWS.value,
        "resource": "SQS",
        "resource_type": "Queue"
    })

    url = aws_interface.get_endpoint("test_workflow", SwitchboardComponent.ExecutorQueue)
    assert url == "https://sqs/mock/url"


def test_get_endpoint_missing_item_raises(aws_interface):
    with pytest.raises(Exception):
        aws_interface.get_endpoint("nonexistent", SwitchboardComponent.ExecutorQueue)





# cloud.py
@mock_aws
def test_AWS_db_connect(aws_credentials):
    # The mock_aws decorator handles the setup and teardown of the mock environment
    db_resource = AWS_db_connect()
    assert db_resource is not None
    # You can add more assertions here to verify the resource, e.g., check its type
    assert 'boto3.resources' in str(type(db_resource))

@mock_aws
def test_AWS_message_push(aws_credentials):
    # Set up the SQS client and create a queue for testing
    sqs = boto3.client("sqs", region_name="us-east-1")
    queue_name = "test-queue"
    queue_url = sqs.create_queue(QueueName=queue_name)["QueueUrl"]

    # The message to be sent
    message_body = "Test message body"

    # Call the function to be tested
    response = AWS_message_push(endpoint=queue_url, msg=message_body)

    # Assertions to verify the message was sent successfully
    assert response is not None
    assert "MessageId" in response
    assert "ResponseMetadata" in response
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    # Verify the message content by receiving it from the queue
    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)["Messages"]
    assert len(messages) == 1
    assert messages[0]["Body"] == message_body



