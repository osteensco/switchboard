# AWS Demo

This is a demo of Switchboard running on AWS.

## Prerequisites

- Python 3.11+
- Terraform
- An AWS account with credentials configured

## Setup for Administrators

Before a developer can deploy the demo, an administrator must create an IAM role with the necessary permissions.

1.  **Create the IAM Policy:**

    Create an IAM policy using the contents of the `iam_policy.json` file in this directory. You can do this through the AWS Management Console or with the AWS CLI:

    ```bash
    aws iam create-policy --policy-name switchboard-demo-policy --policy-document file://iam_policy.json
    ```

2.  **Create the IAM Role:**

    Create an IAM role that the Lambda functions will assume. This role must have a trust relationship with the Lambda service.

    ```bash
    aws iam create-role --role-name switchboard-demo-role --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'
    ```

3.  **Attach the Policy to the Role:**

    Attach the policy you created to the new role.

    ```bash
    aws iam attach-role-policy --role-name switchboard-demo-role --policy-arn <your-policy-arn>
    ```

    Replace `<your-policy-arn>` with the ARN of the policy you created in the first step.

4.  **Provide the Role ARN to the Developer:**

    The developer will need the ARN of the role you just created to deploy the demo. You can get the ARN with the following command:

    ```bash
    aws iam get-role --role-name switchboard-demo-role --query 'Role.Arn' --output text
    ```

## Deployment for Developers

Before you can deploy the demo, you need to configure your AWS credentials.

1.  **Configure AWS CLI:**

    If you haven't already, configure the AWS CLI with your credentials. You will need an access key and secret key from your administrator.

    ```bash
    aws configure
    ```

    Your administrator should grant you permissions to manage Lambda, SQS, and DynamoDB resources. The specific permissions required are listed in the "Developer IAM Policy" section below.

## Developer IAM Policy

An administrator must attach a policy with the following permissions to your IAM user or role. This policy grants the minimum permissions required to deploy and manage the demo resources using Terraform.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ManageLambdaAndEventSources",
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:CreateEventSourceMapping",
                "lambda:DeleteEventSourceMapping",
                "lambda:GetEventSourceMapping",
                "lambda:UpdateEventSourceMapping",
                "lambda:TagResource"
            ],
            "Resource": "arn:aws:lambda:*:<aws-account-id>:function:switchboard-demo-*"
        },
        {
            "Sid": "ManageSQS",
            "Effect": "Allow",
            "Action": [
                "sqs:CreateQueue",
                "sqs:DeleteQueue",
                "sqs:GetQueueAttributes",
                "sqs:SetQueueAttributes",
                "sqs:TagQueue"
            ],
            "Resource": "arn:aws:sqs:*:<aws-account-id>:switchboard-demo-*"
        },
        {
            "Sid": "ManageDynamoDB",
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DeleteTable",
                "dynamodb:DescribeTable",
                "dynamodb:TagResource"
            ],
            "Resource": "arn:aws:dynamodb:*:<aws-account-id>:table/switchboard-demo-state"
        },
        {
            "Sid": "PassRoleForLambda",
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "arn:aws:iam::<aws-account-id>:role/switchboard-demo-role"
        }
    ]
}
```

2.  **Install local dependencies:**
    
    This installs the necessary Python dependencies for the `trigger_workflow.py` script to work.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Package the Lambda functions:**

    ```bash
    bash ./package.sh
    ```

4.  **Deploy the infrastructure:**

    You will be prompted to enter the IAM role ARN provided by your administrator.

    ```bash
    cd terraform && terraform init && terraform validate && terraform apply && terraform output -json > output.json && cd ..
    ```

5.  **Populate the resources database:**

    ```bash
    python register_resources.py
    ```

## Usage

You can trigger the workflow by running the `trigger_workflow.py` script:

```bash
python trigger_workflow.py
```
