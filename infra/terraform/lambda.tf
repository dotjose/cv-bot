resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = local.lambda_image_effective
  publish       = true

  memory_size = 1536
  timeout     = 120

  environment {
    variables = {
      CHAT_S3_BUCKET   = aws_s3_bucket.memory.id
      CHAT_S3_PREFIX   = "chat/"
      FRONTEND_BUCKET  = aws_s3_bucket.frontend.id

      OPENROUTER_API_KEY = var.openrouter_api_key
      QDRANT_URL         = var.qdrant_url
      QDRANT_API_KEY     = var.qdrant_api_key

      PROJECT        = var.project
      DEPLOYMENT_ENV = var.deployment_env
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_memory_s3,
  ]
}

resource "aws_lambda_alias" "live" {
  name             = "live"
  function_name    = aws_lambda_function.api.function_name
  function_version = aws_lambda_function.api.version
}
