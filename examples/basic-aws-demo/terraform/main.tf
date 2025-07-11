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

  project_name = var.project_name
  environment  = var.environment
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

  iam_role_arn         = module.iam.lambda_role_arn
  invocation_queue_arn = module.sqs.invocation_queue_arn
  invocation_queue_url = module.sqs.invocation_queue_url
  executor_queue_arn   = module.sqs.executor_queue_arn
  executor_queue_url   = module.sqs.executor_queue_url
}
