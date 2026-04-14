locals {
  name_prefix = "${var.project}-${var.deployment_env}"

  # Lambda + HTTP API are created only after CI sets lambda_image_uri (real ECR URI).
  lambda_enabled = trimspace(var.lambda_image_uri) != ""

  openrouter_api_key_valid = length(trimspace(var.openrouter_api_key)) > 0
}
