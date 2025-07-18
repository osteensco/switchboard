output "invocation_queue_url" {
  description = "The URL of the invocation SQS queue."
  value       = aws_sqs_queue.invocation_queue.url
}

output "executor_queue_url" {
  description = "The URL of the executor SQS queue."
  value       = aws_sqs_queue.executor_queue.url
}

output "invocation_queue_arn" {
  description = "The ARN of the invocation SQS queue."
  value       = aws_sqs_queue.invocation_queue.arn
}

output "executor_queue_arn" {
  description = "The ARN of the executor SQS queue."
  value       = aws_sqs_queue.executor_queue.arn
}