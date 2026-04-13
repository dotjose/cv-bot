# -----------------------------------------------------------------------------
# MVP: S3 (UI + chat memory) · CloudFront · ECR · Lambda (container) · HTTP API
# -----------------------------------------------------------------------------

terraform {
  required_version = ">= 1.9.0"

  backend "s3" {
    key     = "cv-bot/terraform.tfstate"
    encrypt = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# Random suffix (globally unique bucket names)
# -----------------------------------------------------------------------------

resource "random_id" "suffix" {
  byte_length = 3
}

# -----------------------------------------------------------------------------
# S3 — frontend (static Next export) + chat memory (JSON per session)
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project}-frontend-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "chat_memory" {
  bucket = "${var.project}-chat-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "chat_memory" {
  bucket = aws_s3_bucket.chat_memory.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "chat_memory" {
  bucket = aws_s3_bucket.chat_memory.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "chat_memory" {
  bucket = aws_s3_bucket.chat_memory.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "chat_memory" {
  bucket = aws_s3_bucket.chat_memory.id
  rule {
    id     = "abort-incomplete-mpu"
    status = "Enabled"
    filter { prefix = "" }
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# CloudFront OAC → private frontend bucket

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project}-frontend-oac"
  description                       = "OAC for ${var.project} static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "frontend_oac" {
  statement {
    sid    = "AllowCloudFrontRead"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_oac.json
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${var.project} static export"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Managed-CachingOptimized
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# -----------------------------------------------------------------------------
# ECR — Lambda container image (tag = commit SHA in CI, never :latest alone)
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "api" {
  name                 = "${var.project}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# -----------------------------------------------------------------------------
# Lambda — in-place image updates only (same resource, new image_uri)
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda" {
  name = "${var.project}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_chat_s3" {
  statement {
    sid       = "ChatMemoryList"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.chat_memory.arn]
  }

  statement {
    sid       = "ChatMemoryObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.chat_memory.arn}/*"]
  }
}

resource "aws_iam_role_policy" "lambda_chat_s3" {
  name   = "${var.project}-lambda-chat-s3"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_chat_s3.json
}

locals {
  lambda_env = {
    OPENROUTER_API_KEY         = var.openrouter_api_key
    OPENROUTER_CHAT_MODEL      = var.openrouter_chat_model
    OPENROUTER_EMBEDDING_MODEL = var.openrouter_embedding_model
    OPENROUTER_SITE_URL        = var.openrouter_site_url
    OPENROUTER_SITE_NAME       = var.openrouter_site_name
    OPENROUTER_MAX_RETRIES     = tostring(var.openrouter_max_retries)
    OPENROUTER_RETRY_BASE_MS   = tostring(var.openrouter_retry_base_ms)
    QDRANT_URL                 = var.qdrant_url
    QDRANT_API_KEY             = var.qdrant_api_key
    QDRANT_VECTOR_SIZE         = tostring(var.qdrant_vector_size)
    RAG_TOP_K                  = tostring(var.rag_top_k)
    RAG_PREFETCH               = tostring(var.rag_prefetch)
    CORS_ORIGIN                = var.cors_origin
    PROFILE_DATA_PATH          = "/var/task/data/dynamic-profile.json"
    PROFILE_IDENTITY_NAME      = var.profile_identity_name
    CHAT_S3_BUCKET             = aws_s3_bucket.chat_memory.id
    CHAT_S3_PREFIX             = "chat/"
    AWS_REGION                 = var.aws_region
    CHAT_SESSION_HEADER        = "X-Session-Id"
  }
}

resource "aws_lambda_function" "api" {
  count = var.enable_api ? 1 : 0

  function_name = "${var.project}-api"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.lambda_image_uri

  memory_size = var.lambda_memory_mb
  timeout     = var.lambda_timeout_seconds

  environment {
    variables = local.lambda_env
  }

  # Updating image_uri updates the Lambda in place (new revision); do not use :latest-only tags in CI.
  lifecycle {
    prevent_destroy = false
    precondition {
      condition     = !var.enable_api || var.lambda_image_uri != ""
      error_message = "When enable_api is true, set lambda_image_uri to the ECR image (e.g. account.dkr.ecr.region.amazonaws.com/cv-bot-api:<git-sha>). Do not deploy with an empty URI."
    }
  }
}

# -----------------------------------------------------------------------------
# API Gateway HTTP API → Lambda
# -----------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "http" {
  count = var.enable_api ? 1 : 0

  name          = "${var.project}-http"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  count = var.enable_api ? 1 : 0

  api_id                 = aws_apigatewayv2_api.http[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api[0].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  count = var.enable_api ? 1 : 0

  api_id    = aws_apigatewayv2_api.http[0].id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_apigatewayv2_route" "root" {
  count = var.enable_api ? 1 : 0

  api_id    = aws_apigatewayv2_api.http[0].id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_apigatewayv2_stage" "default" {
  count = var.enable_api ? 1 : 0

  api_id      = aws_apigatewayv2_api.http[0].id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  count = var.enable_api ? 1 : 0

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http[0].execution_arn}/*/*"
}
