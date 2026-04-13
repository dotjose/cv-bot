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
  }
}
