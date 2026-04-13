locals {
  name_prefix = "${var.project}-${var.deployment_env}"

  # Lambda requires an existing image URI. Before the first ECR push, use the AWS
  # public Lambda Python base image so a cold `terraform apply` can create the full stack.
  lambda_bootstrap_image = "public.ecr.aws/lambda/python:3.12-x86_64"
  lambda_image_effective = trimspace(var.lambda_image_uri) != "" ? var.lambda_image_uri : local.lambda_bootstrap_image
}
