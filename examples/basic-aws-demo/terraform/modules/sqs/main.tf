resource "aws_sqs_queue" "invocation_queue" {
  name = "${var.project_name}-invocation-queue-${var.environment}"
}

resource "aws_sqs_queue" "executor_queue" {
  name = "${var.project_name}-executor-queue-${var.environment}"
}
