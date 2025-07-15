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

## Deployment Steps

1.  **Navigate to the Terraform directory:**
    ```bash
    cd examples/aws-demo/terraform
    ```

2.  **Initialize Terraform:**
    This command downloads the necessary AWS provider plugin.
    ```bash
    terraform init
    ```

3.  **Review the plan (Optional but Recommended):**
    This command shows you what Terraform will create, modify, or destroy.
    ```bash
    terraform plan
    ```

4.  **Apply the Terraform configuration:**
    This command will provision the AWS resources. Type `yes` when prompted to confirm.
    ```bash
    terraform apply
    ```

## Running the Demo Workflow

Once deployed, you can trigger the sample workflow. The `tasks.py` file defines a simple `hello_world_task`.

*(Instructions for triggering the workflow will be added here once the CLI or a direct invocation method is available.)*

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
