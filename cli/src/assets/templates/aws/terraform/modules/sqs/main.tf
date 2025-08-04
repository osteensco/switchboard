resource "aws_sqs_queue" "invocation_queue" {
  name = "switchboard-invocation-queue-${var.workflow_name}"
}

resource "aws_sqs_queue" "executor_queue" {
  name = "switchboard-executor-queue-${var.workflow_name}"
}
