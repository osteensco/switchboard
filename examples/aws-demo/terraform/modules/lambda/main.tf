resource "aws_lambda_function" "workflow_lambda" {
  function_name = "${var.project_name}-workflow-${var.environment}"
  role          = var.switchboard_role_arn
  handler       = "src.workflow.workflow_handler"
  runtime       = "python3.11"
  filename      = "../lambda_package.zip"
  timeout       = 30

  environment {
    variables = {
      INVOCATION_QUEUE_URL = var.invocation_queue_url
      EXECUTOR_QUEUE_URL   = var.executor_queue_url
    }
  }

  source_code_hash = filebase64sha256("../lambda_package.zip")
}

resource "aws_lambda_function" "executor_lambda" {
  function_name = "${var.project_name}-executor-${var.environment}"
  role          = var.switchboard_role_arn
  handler       = "src.executor.lambda_handler"
  runtime       = "python3.11"
  filename      = "../lambda_package.zip"
  timeout       = 30

  environment {
    variables = {
      INVOCATION_QUEUE_URL = var.invocation_queue_url
    }
  }

  source_code_hash = filebase64sha256("../lambda_package.zip")
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
