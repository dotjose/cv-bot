output "frontend_bucket" {
  value       = aws_s3_bucket.frontend.id
  description = "Next.js static export target."
}

output "memory_bucket" {
  value       = aws_s3_bucket.memory.id
  description = "Chat history at s3://<bucket>/chat/{sessionId}.json (Lambda only)."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository URL for docker push."
}

output "http_api_endpoint" {
  value       = local.lambda_enabled ? aws_apigatewayv2_api.api[0].api_endpoint : ""
  description = "HTTP API base URL for NEXT_PUBLIC_API_URL (empty until lambda_image_uri is applied)."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "CloudFront invalidation target."
}

output "distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "Same as cloudfront_distribution_id; use with create-invalidation."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "Public site: https://<this-value> (not cloudfront.amazonaws.com)."
}
