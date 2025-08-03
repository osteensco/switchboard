variable "iam_role_arn" {
  description = "The ARN of the pre-existing IAM role for the Lambda functions."
  type        = string
}

variable "aws_region" {
  description = "The AWS region to deploy the resources to."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "switchboard"
}

variable "environment" {
  description = "The environment to deploy to."
  type        = string
  default     = "dev"
}

variable "workflow_name" {
  description = "The name of the workflow."
  type = string
  default = "my-workflow"
}

variable "workflow_handler" {
  description = "The handler for the workflow lambda."
  type        = string
}

variable "workflow_runtime" {
  description = "The runtime for the workflow lambda."
  type        = string
}

variable "executor_handler" {
  description = "The handler for the executor lambda."
  type        = string
}

variable "executor_runtime" {
  description = "The runtime for the executor lambda."
  type        = string
}
