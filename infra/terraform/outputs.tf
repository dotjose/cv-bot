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
  value       = aws_apigatewayv2_api.api.api_endpoint
  description = "HTTP API base URL for NEXT_PUBLIC_API_URL."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "CloudFront invalidation target."
}
