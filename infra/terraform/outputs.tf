output "frontend_bucket" {
  value       = aws_s3_bucket.frontend.id
  description = "Upload Next.js `out/` here (e.g. aws s3 sync apps/web/out s3://... --delete)."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "Static site URL (set CORS_ORIGIN / NEXT_PUBLIC_API_URL as needed)."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "Use for cache invalidation after deploy."
}

output "chat_memory_bucket" {
  value       = aws_s3_bucket.chat_memory.id
  description = "Chat transcripts at chat/{session_id}.json (CHAT_S3_BUCKET on Lambda)."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "docker tag & push target for the API image."
}

output "http_api_endpoint" {
  value       = length(aws_apigatewayv2_api.http) > 0 ? aws_apigatewayv2_api.http[0].api_endpoint : ""
  description = "Base URL for NEXT_PUBLIC_API_URL (no trailing slash). Empty if API Gateway not in state."
}
