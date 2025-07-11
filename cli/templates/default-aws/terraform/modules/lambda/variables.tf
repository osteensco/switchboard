variable "project_name" {
  description = "The name of the project."
  type        = string
}

variable "environment" {
  description = "The environment to deploy to."
  type        = string
}

variable "iam_role_arn" {
  description = "The ARN of the IAM role for the Lambda functions."
  type        = string
}

variable "invocation_queue_arn" {
  description = "The ARN of the invocation queue."
  type        = string
}

variable "invocation_queue_url" {
  description = "The URL of the invocation queue."
  type        = string
}

variable "executor_queue_arn" {
  description = "The ARN of the executor queue."
  type        = string
}

variable "executor_queue_url" {
  description = "The URL of the executor queue."
  type        = string
}
