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
}

module "sqs" {
  source = "./modules/sqs"
}

module "lambda" {
  source = "./modules/lambda"

  switchboard_role_arn         = module.iam.switchboard_role_arn
  invocation_queue_arn = module.sqs.invocation_queue_arn
  invocation_queue_url = module.sqs.invocation_queue_url
  executor_queue_arn   = module.sqs.executor_queue_arn
  executor_queue_url   = module.sqs.executor_queue_url

  workflow_handler = var.workflow_handler
  workflow_runtime = var.workflow_runtime
  executor_handler = var.executor_handler
  executor_runtime = var.executor_runtime
}
