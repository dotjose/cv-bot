variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "us-east-1"
}

variable "project" {
  type        = string
  description = "Short name prefix for resources."
  default     = "cv-bot"
}

variable "enable_api" {
  type        = bool
  default     = true
  description = "Set false on first apply to create S3/CloudFront/ECR only; push an image, then apply again with true."
}

variable "lambda_image_uri" {
  type        = string
  default     = ""
  description = "Full ECR image URI including tag. Required when enable_api is true."
}

variable "openrouter_api_key" {
  type        = string
  sensitive   = true
  description = "OpenRouter API key (TF_VAR_openrouter_api_key in CI)."
}

variable "openrouter_chat_model" {
  type    = string
  default = "openai/gpt-4o-mini"
}

variable "openrouter_embedding_model" {
  type    = string
  default = "openai/text-embedding-3-small"
}

variable "openrouter_site_url" {
  type    = string
  default = ""
}

variable "openrouter_site_name" {
  type    = string
  default = "cv-bot"
}

variable "openrouter_max_retries" {
  type    = number
  default = 3
}

variable "openrouter_retry_base_ms" {
  type    = number
  default = 400
}

variable "qdrant_url" {
  type        = string
  description = "Qdrant Cloud HTTPS URL."
}

variable "qdrant_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Qdrant API key (empty if local / open instance)."
}

variable "qdrant_vector_size" {
  type    = number
  default = 1536
}

variable "rag_top_k" {
  type    = number
  default = 6
}

variable "rag_prefetch" {
  type    = number
  default = 24
}

variable "cors_origin" {
  type        = string
  default     = "*"
  description = "Value for CORS_ORIGIN on the Lambda (e.g. https://d123.cloudfront.net once known)."
}

variable "profile_identity_name" {
  type    = string
  default = "Eyosiyas Tadele"
}

variable "lambda_memory_mb" {
  type    = number
  default = 1536
}

variable "lambda_timeout_seconds" {
  type    = number
  default = 120
}
