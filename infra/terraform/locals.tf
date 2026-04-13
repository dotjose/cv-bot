locals {
  name_prefix = "${var.project}-${var.deployment_env}"

  # Placeholder until CI sets lambda_image_uri; must be a valid Lambda base image on public.ecr.aws (matches Dockerfile).
  lambda_bootstrap_image = "public.ecr.aws/lambda/python:3.11"
  lambda_image_effective = trimspace(var.lambda_image_uri) != "" ? var.lambda_image_uri : local.lambda_bootstrap_image
}
