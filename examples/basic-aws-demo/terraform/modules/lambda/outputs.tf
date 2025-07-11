output "workflow_lambda_name" {
  description = "The name of the workflow Lambda function."
  value       = aws_lambda_function.workflow_lambda.function_name
}

output "executor_lambda_name" {
  description = "The name of the executor Lambda function."
  value       = aws_lambda_function.executor_lambda.function_name
}
