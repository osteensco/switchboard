
# Setup for Administrators

This doc provides details for cloud admins to set up appropriate permissions for developers to start using Switchboard in production.

## AWS

Before a developer can create and deploy workflows with Switchboard, an administrator must create an IAM role with the necessary permissions.

1.  **Create the IAM Policy:**

    Create an IAM policy using the contents of the `iam_policy.json` file in this directory. 
    You can do this through the AWS Management Console or with the AWS CLI:

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

