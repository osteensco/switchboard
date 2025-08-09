resource "aws_lambda_function" "workflow_lambda" {
  function_name = "switchboard-workflow-${var.workflow_name}"
  role          = var.switchboard_role_arn
  handler       = var.workflow_handler
  runtime       = var.workflow_runtime
  filename      = "../workflow/workflow_lambda.zip"
  timeout       = 30

  environment {
    variables = {
      INVOCATION_QUEUE_URL = var.invocation_queue_url
      EXECUTOR_QUEUE_URL   = var.executor_queue_url
    }
  }

  source_code_hash = filebase64sha256("../workflow/workflow_lambda.zip")
}

resource "aws_lambda_function" "executor_lambda" {
  function_name = "switchboard-executor-${var.workflow_name}"
  role          = var.switchboard_role_arn
  handler       = var.executor_handler
  runtime       = var.executor_runtime
  filename      = "../executor/executor_lambda.zip"
  timeout       = 30

  environment {
    variables = {
      INVOCATION_QUEUE_URL = var.invocation_queue_url
    }
  }

  source_code_hash = filebase64sha256("../executor/executor_lambda.zip")
}

resource "aws_lambda_event_source_mapping" "invocation_queue_mapping" {
  event_source_arn = var.invocation_queue_arn
  function_name    = aws_lambda_function.workflow_lambda.arn
}

resource "aws_lambda_event_source_mapping" "executor_queue_mapping" {
  event_source_arn = var.executor_queue_arn
  function_name    = aws_lambda_function.executor_lambda.arn
  batch_size       = 1
  enabled          = true
}
