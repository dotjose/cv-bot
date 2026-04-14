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
  description = "OpenRouter API key (Lambda OPENROUTER_API_KEY). Set TF_VAR_openrouter_api_key."

  validation {
    condition     = length(trimspace(var.openrouter_api_key)) > 0
    error_message = "OPENROUTER_API_KEY is required and cannot be empty."
  }
}

variable "qdrant_url" {
  type        = string
  sensitive   = false
  description = "Qdrant HTTPS URL (Lambda QDRANT_URL). Set TF_VAR_qdrant_url."

  validation {
    condition     = length(trimspace(var.qdrant_url)) > 0
    error_message = "QDRANT_URL is required and cannot be empty."
  }
}

variable "qdrant_api_key" {
  type        = string
  sensitive   = true
  description = "Qdrant API key (Lambda QDRANT_API_KEY). Set TF_VAR_qdrant_api_key."

  validation {
    condition     = length(trimspace(var.qdrant_api_key)) > 0
    error_message = "QDRANT_API_KEY is required and cannot be empty."
  }
}
