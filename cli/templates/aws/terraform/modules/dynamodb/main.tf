resource "aws_dynamodb_table" "state_table" {
  name           = "SwitchboardState"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "name"
  range_key      = "run_id"

  attribute {
    name = "name"
    type = "S"
  }

  attribute {
    name = "run_id"
    type = "N"
  }
}

resource "aws_dynamodb_table" "resources_table" {
  name           = "SwitchboardResources"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "component"
  range_key      = "name"

  attribute {
    name = "component"
    type = "S"
  }

  attribute {
    name = "name"
    type = "S"
  }
}
