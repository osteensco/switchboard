output "workflow_lambda_name" {
  description = "The name of the workflow Lambda function."
  value       = module.lambda.workflow_lambda_name
}

output "executor_lambda_name" {
  description = "The name of the executor Lambda function."
  value       = module.lambda.executor_lambda_name
}

output "invocation_queue_url" {
  description = "The URL of the invocation SQS queue."
  value       = module.sqs.invocation_queue_url
}

output "executor_queue_url" {
  description = "The URL of the executor SQS queue."
  value       = module.sqs.executor_queue_url
}

output "state_table_name" {
  description = "The name of the DynamoDB state table."
  value       = module.dynamodb.state_table_name
}

output "resources_table_name" {
  description = "The name of the DynamoDB resources table."
  value       = module.dynamodb.resources_table_name
}
