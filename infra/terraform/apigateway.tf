resource "aws_apigatewayv2_api" "api" {
  count = local.lambda_enabled ? 1 : 0

  name          = "${local.name_prefix}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  count = local.lambda_enabled ? 1 : 0

  api_id                 = aws_apigatewayv2_api.api[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_alias.live[0].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  count = local.lambda_enabled ? 1 : 0

  api_id    = aws_apigatewayv2_api.api[0].id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_apigatewayv2_route" "root" {
  count = local.lambda_enabled ? 1 : 0

  api_id    = aws_apigatewayv2_api.api[0].id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_apigatewayv2_stage" "default" {
  count = local.lambda_enabled ? 1 : 0

  api_id      = aws_apigatewayv2_api.api[0].id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  count = local.lambda_enabled ? 1 : 0

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api[0].function_name
  qualifier     = aws_lambda_alias.live[0].name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api[0].execution_arn}/*/*"
}
