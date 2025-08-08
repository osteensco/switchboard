# AWS Demo

This is a demo of Switchboard running on AWS.

## Prerequisites

- Python 3.11+
- Terraform
- An AWS account with credentials configured
- Be sure your working direcctory is examples/aws-demo

## Setup for Administrators

Before a developer can deploy the demo, an administrator must create an IAM role with the necessary permissions. 
[Details for the IAM resources setup can be found here.](https://github.com/osteensco/switchboard/blob/main/docs/admin.md)

## Deployment for Developers

Before you can deploy the demo, you need to configure your AWS credentials.

1.  **Configure AWS CLI:**

    If you haven't already, configure the AWS CLI with your credentials. You will need an access key and secret key from your administrator.

    ```bash
    aws configure
    ```

    Your administrator should grant you permissions to manage Lambda, SQS, and DynamoDB resources. 
    The specific permissions required are listed in the "Developer IAM Policy" section of the admin docs.

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
