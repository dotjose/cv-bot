variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
}

variable "project" {
  type        = string
  description = "Short name prefix for resources."
}

variable "deployment_env" {
  type        = string
  description = "Environment segment in resource names; matches GitHub Environment (staging | production)."
  validation {
    condition     = contains(["staging", "production"], var.deployment_env)
    error_message = "deployment_env must be \"staging\" or \"production\"."
  }
}

variable "lambda_image_uri" {
  type        = string
  description = "Full ECR image URI including tag. Empty = create ECR/S3/CloudFront/IAM only; CI sets this after docker push, then apply again."
  default     = ""
}

variable "openrouter_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "OpenRouter API key for Lambda env. Prefer TF_VAR_openrouter_api_key (e.g. GitHub OPENROUTER_API_KEY) or another secret source; may be empty if injected elsewhere."
}

variable "qdrant_url" {
  type        = string
  default     = ""
  description = "Qdrant HTTPS URL (empty string if unused)."
}

variable "qdrant_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Qdrant API key (empty string if unused)."
}
