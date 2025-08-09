variable "switchboard_role_arn" {
  description = "The ARN of the pre-existing IAM role for the Lambda functions."
  type        = string
}

variable "aws_region" {
  description = "The AWS region to deploy the resources to."
  type        = string
  default     = "us-east-1"
}

variable "workflow_name" {
  description = "The name of the workflow."
  type = string
}

variable "workflow_handler" {
  description = "The handler for the workflow lambda."
  type        = string
}

variable "executor_handler" {
  description = "The handler for the executor lambda."
  type        = string
}

variable "runtime" {
  description = "The runtime for the workflow and executor lambdas."
  type        = string
}
