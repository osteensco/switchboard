
resource "aws_lambda_function" "endpoint_lambda" {
  function_name = "switchboard-executor-${var.workflow_name}"
  role          = var.switchboard_role_arn
  handler       = var.endpoint_handler
  runtime       = var.runtime
  filename      = "../trigger/endpoint_lambda.zip"
  timeout       = 30

  environment {
    variables = {
      INVOCATION_QUEUE_URL = var.invocation_queue_url
    }
  }
