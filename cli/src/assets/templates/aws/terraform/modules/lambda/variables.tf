variable "workflow_name" {
  description = "The name of the workflow."
  type        = string
}

variable "switchboard_role_arn" {
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

variable "workflow_handler" {
  description = "The handler for the workflow lambda."
  type        = string
}

variable "executor_handler" {
  description = "The handler for the executor lambda."
  type        = string
}

variable "runtime" {
  description = "The runtime for lambdas."
  type        = string
}


