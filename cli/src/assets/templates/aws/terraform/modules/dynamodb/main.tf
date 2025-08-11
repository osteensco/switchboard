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

resource "aws_dynambodb_table_item" "resource_items" {
  for_each = { for item in var.switchboard_resources : item.component => item}
  table_name = aws_dynamodb_table.resources_table.name
  hash_key = aws_dynamodb_table.resources_table.hash_key

  item = jsonencode({
        component = each.value.component
        name = each.value.name
        url = each.value.url
        cloud = each.value.cloud
        resource = each.value.resource
        resource_type = each.value.resource_type
  })
}
