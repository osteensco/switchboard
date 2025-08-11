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

resource "aws_dynamodb_table_item" "resource_items" {
  for_each = { for i in var.switchboard_resources : i.component => i}
  table_name = aws_dynamodb_table.resources_table.name
  hash_key = aws_dynamodb_table.resources_table.hash_key
  range_key  = aws_dynamodb_table.resources_table.range_key

  item = jsonencode({
    component      = { S = each.value.component }
    name           = { S = each.value.name }
    url            = { S = each.value.url }
    cloud          = { S = each.value.cloud }
    resource       = { S = each.value.resource }
    resource_type  = { S = each.value.resource_type }

  })
}
