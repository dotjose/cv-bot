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
  description = "Environment segment in resource names (e.g. staging, prod)."
  validation {
    condition     = contains(["staging", "prod"], var.deployment_env)
    error_message = "deployment_env must be \"staging\" or \"prod\"."
  }
}

variable "lambda_image_uri" {
  type        = string
  description = "Full ECR image URI including tag. Leave empty to use the AWS public Lambda Python image until the first app image is pushed."
  default     = ""
}

variable "openrouter_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "OpenRouter API key."
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
