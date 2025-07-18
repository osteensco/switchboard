output "state_table_name" {
  description = "The name of the DynamoDB state table."
  value       = aws_dynamodb_table.state_table.name
}

output "resources_table_name" {
  description = "The name of the DynamoDB resources table."
  value       = aws_dynamodb_table.resources_table.name
}