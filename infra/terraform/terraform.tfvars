# Non-secret defaults. CI overrides enable_api + lambda_image_uri via -var on apply.
# Copy and extend locally; do not commit secrets here (use TF_VAR_* or *.auto.tfvars gitignored).

project     = "cv-bot"
aws_region  = "us-east-1"
enable_api  = false
cors_origin = "*"
