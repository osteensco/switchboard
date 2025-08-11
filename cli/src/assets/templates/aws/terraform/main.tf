terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "iam" {
  source = "./modules/iam"

  switchboard_role_arn = var.switchboard_role_arn
}

module "dynamodb" {
  source = "./modules/dynamodb"
  switchboard_resources = [
   # TODO 
   #  Handle adding triggers
    {
        component = "ExecutorQueue"
        name = var.workflow_name
        url = module.sqs.executor_queue_url
        cloud = "AWS"
        resource = "SQS"
        resource_type = "QUEUE"
    },
    {
        component = "InvocationQueue",
        name = var.workflow_name,
        url = module.sqs.invocation_queue_url
        cloud = "AWS"
        resource = "SQS"
        resource_type = "QUEUE"
    },
    {
        component = "ExecutorFunction"
        name = var.workflow_name
        url = module.lambda.executor_lambda_name
        cloud = "AWS"
        resource = "LAMBDA"
        resource_type = "COMPUTE"
    },
    {
        component = "WorkflowFunction",
        name = var.workflow_name,
        url = module.lambda.workflow_lambda_name
        cloud = "AWS"
        resource = "LAMBDA"
        resource_type = "COMPUTE"
    }
    
  ]

}

module "sqs" {
  source = "./modules/sqs"
  workflow_name = var.workflow_name
}

module "lambda" {
  source = "./modules/lambda"

  switchboard_role_arn         = module.iam.switchboard_role_arn
  invocation_queue_arn = module.sqs.invocation_queue_arn
  invocation_queue_url = module.sqs.invocation_queue_url
  executor_queue_arn   = module.sqs.executor_queue_arn
  executor_queue_url   = module.sqs.executor_queue_url
  
  workflow_name = var.workflow_name
  workflow_handler = var.workflow_handler
  executor_handler = var.executor_handler
  runtime = var.runtime

}
