
# Setup for Administrators

This doc provides details for cloud admins to set up appropriate permissions for developers to start using Switchboard in production.

## AWS

The Switchboard AWS IAM setup consists of:

 - **IAM Policy for Lambda Functions:**
    Grants runtime permissions for the Lambda functions used in Switchboard workflows. This includes:
    - Reading/writing workflow state in DynamoDB.
    - Sending and receiving messages via SQS.
    - Writing logs to CloudWatch for monitoring and troubleshooting.

 - **IAM Role for Lambda Functions:**
    - A role that the Lambda service can assume at runtime, with the Lambda policy attached.

 - **IAM Policy for Developers:**
    Grants developers the minimum permissions required to:
    - Create, update, and delete Lambda functions and event source mappings.
    - Manage associated SQS queues and DynamoDB tables.
    - Pass the Lambda execution role to new functions during deployment.



1.  **Create the Lambda IAM Policy:**
    
    In any new switchboard project created using the CLI tool, there should be a a file named `iam_policy.json` with the following contents.

    ```json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowDynamoDBReadWrite",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:dynamodb:*:*:table/Switchboard*"
            },
            {
                "Sid": "AllowSQSActions",
                "Action": [
                    "sqs:SendMessage",
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:sqs:*:*:switchboard-*"
            },
            {
                "Sid": "AllowLogging",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Effect": "Allow",
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }
    ```
    
    Create an IAM policy using the contents of the `iam_policy.json`. 
    You can do this through the AWS Management Console or with the AWS CLI:

    ```bash
    aws iam create-policy --policy-name switchboard-policy --policy-document file://iam_policy.json
    ```

2.  **Create the Lambda IAM Role:**

    Create an IAM role that the Lambda functions will assume. This role must have a trust relationship with the Lambda service.

    ```bash
    aws iam create-role --role-name switchboard-role --assume-role-policy-document '{
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
    aws iam attach-role-policy --role-name switchboard-role --policy-arn <your-policy-arn>
    ```

    Replace `<your-policy-arn>` with the ARN of the policy you created in the first step.

4.  **Provide the Role ARN to the Developer:**

    The developer will need the ARN of the role you just created to deploy a switchboard workflow to production. You can get the ARN with the following command:

    ```bash
    aws iam get-role --role-name switchboard-role --query 'Role.Arn' --output text
    ```


5. **Developer IAM Policy:**


An administrator must create a policy or a group with the following permissions.
These are the minimum permissions required to deploy and manage a switchboard workflow's resources using Terraform.

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
                "lambda:TagResource",
                "lambda:ListTags",
				"lambda:ListVersionsByFunction",
                "lambda:GetFunctionCodeSigningConfig"
            ],
            "Resource": [
                "arn:aws:lambda:*:<aws-account-id>:function:switchboard-*",
                "arn:aws:lambda:*:<aws-account-id>:event-source-mapping:*"
            ]
        },
        {
          "Sid": "ManageLambdaGetEventSourceMapping",
          "Effect": "Allow",
          "Action": "lambda:GetEventSourceMapping",
          "Resource": "*"
        },
        {
            "Sid": "ManageSQS",
            "Effect": "Allow",
            "Action": [
                "sqs:CreateQueue",
                "sqs:DeleteQueue",
                "sqs:GetQueueAttributes",
                "sqs:SetQueueAttributes",
                "sqs:TagQueue",
                "sqs:ListQueueTags"
            ],
            "Resource": "arn:aws:sqs:*:<aws-account-id>:switchboard-*"
        },
        {
            "Sid": "ManageDynamoDB",
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DeleteTable",
                "dynamodb:DescribeTable",
                "dynamodb:DescribeTimeToLive",
                "dynamodb:DescribeContinuousBackups",
                "dynamodb:TagResource",
                "dynamodb:ListTagsOfResource"

            ],
            "Resource": "arn:aws:dynamodb:*:<aws-account-id>:table/Switchboard*"
        },
        {
            "Sid": "PassGetRole",
            "Effect": "Allow",
            "Action":  [
                "iam:PassRole",
                "iam:GetRole"
            ],
            "Resource": "arn:aws:iam::<aws-account-id>:role/switchboard-role"
        }
    ]
}
```

