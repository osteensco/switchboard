# Basic AWS Demo for Switchboard

This directory contains a basic demonstration of the Switchboard framework deployed on AWS using Terraform.

## Overview

This demo sets up the core AWS infrastructure required for a Switchboard workflow:

*   **IAM Role:** A dedicated IAM role with the necessary permissions for Lambda functions to interact with DynamoDB and SQS.
*   **DynamoDB Tables:**
    *   `SwitchboardState`: Stores the state of ongoing and completed workflows.
    *   `SwitchboardResources`: Stores metadata about Switchboard components (like queue URLs).
*   **SQS Queues:**
    *   `Invocation Queue`: Used to trigger new workflows and receive responses from tasks.
    *   `Executor Queue`: Used to send tasks to the executor Lambda.
*   **Lambda Functions:**
    *   `Workflow Lambda`: Orchestrates the workflow logic.
    *   `Executor Lambda`: Executes individual tasks defined in `tasks.py`.

## Prerequisites

Before deploying this demo, ensure you have the following installed and configured:

1.  **AWS Account:** You need an active AWS account.
2.  **AWS CLI:** Configured with credentials that have permissions to create IAM roles, DynamoDB tables, SQS queues, and Lambda functions.
    *   You can configure your AWS CLI by running `aws configure`.
3.  **Terraform:** Install Terraform CLI (version 1.0+ recommended).
    *   Download from [https://www.terraform.io/downloads](https://www.terraform.io/downloads).
    *   Ensure the `terraform` executable is in your system's PATH.
4.  **Python 3.9+:** Required for the Lambda function code.
5.  **Pip:** The Python package installer.

## Deployment Steps

1.  **Navigate to the example directory:**
    ```bash
    cd examples/aws-demo
    ```

2.  **Run the deployment script:**
    This script will package the Python code and deploy the AWS resources using Terraform.
    ```bash
    ./deploy.sh
    ```

## Running the Demo Workflow

Once deployed, you can trigger and monitor the sample workflow using the `trigger_workflow.py` script.

1.  **Install dependencies:**
    ```bash
    pip install -r ../../sdk/py/requirements.txt
    ```

2.  **Run the trigger script:**
    ```bash
    python trigger_workflow.py
    ```

This will start the workflow and print real-time status updates to your console.

## Cleanup

To destroy all the resources created by this demo (to avoid incurring AWS costs):

1.  **Navigate to the Terraform directory:**
    ```bash
    cd examples/aws-demo/terraform
    ```

2.  **Destroy the resources:**
    This command will remove all resources provisioned by this Terraform configuration. Type `yes` when prompted to confirm.
    ```bash
    terraform destroy
    ```