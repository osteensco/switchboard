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

