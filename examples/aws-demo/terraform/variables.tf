variable "iam_role_arn" {
  description = "The ARN of the pre-existing IAM role for the Lambda functions."
  type        = string
}

variable "aws_region" {
  description = "The AWS region to deploy the resources to."
  type        = string
  default     = "us-east-1" # TODO this should probably be removed and default to the users's cli default
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
  default = "myworkflow"
}
