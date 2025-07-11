output "invocation_queue_arn" {
  description = "The ARN of the invocation queue."
  value       = aws_sqs_queue.invocation_queue.arn
}

output "invocation_queue_url" {
  description = "The URL of the invocation queue."
  value       = aws_sqs_queue.invocation_queue.id
}

output "executor_queue_arn" {
  description = "The ARN of the executor queue."
  value       = aws_sqs_queue.executor_queue.arn
}

output "executor_queue_url" {
  description = "The URL of the executor queue."
  value       = aws_sqs_queue.executor_queue.id
}
