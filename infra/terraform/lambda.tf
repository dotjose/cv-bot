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
      OPENROUTER_API_KEY         = var.openrouter_api_key
      OPENROUTER_CHAT_MODEL      = "openai/gpt-4o-mini"
      OPENROUTER_EMBEDDING_MODEL = "openai/text-embedding-3-small"
      OPENROUTER_SITE_URL        = ""
      OPENROUTER_SITE_NAME       = var.project
      OPENROUTER_MAX_RETRIES     = "3"
      OPENROUTER_RETRY_BASE_MS   = "400"
      QDRANT_URL                 = var.qdrant_url
      QDRANT_API_KEY             = var.qdrant_api_key
      QDRANT_VECTOR_SIZE         = "1536"
      RAG_TOP_K                  = "6"
      RAG_PREFETCH               = "24"
      CORS_ORIGIN                = local.cors_origin
      PROFILE_DATA_PATH          = "/var/task/data/dynamic-profile.json"
      PROFILE_IDENTITY_NAME      = "Eyosiyas Tadele"
      CHAT_S3_BUCKET             = aws_s3_bucket.memory.id
      CHAT_S3_PREFIX             = "chat/"
      AWS_REGION                 = var.aws_region
      CHAT_SESSION_HEADER        = "X-Session-Id"
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
