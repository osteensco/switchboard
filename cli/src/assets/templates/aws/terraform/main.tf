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

  iam_role_arn = var.iam_role_arn
}

module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

module "sqs" {
  source = "./modules/sqs"

  project_name = var.project_name
  environment  = var.environment
}

module "lambda" {
  source = "./modules/lambda"

  project_name = var.project_name
  environment  = var.environment

  iam_role_arn         = module.iam.iam_role_arn
  invocation_queue_arn = module.sqs.invocation_queue_arn
  invocation_queue_url = module.sqs.invocation_queue_url
  executor_queue_arn   = module.sqs.executor_queue_arn
  executor_queue_url   = module.sqs.executor_queue_url

  workflow_handler = var.workflow_handler
  workflow_runtime = var.workflow_runtime
  executor_handler = var.executor_handler
  executor_runtime = var.executor_runtime
}
