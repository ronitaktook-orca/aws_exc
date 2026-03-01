output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (use this for HTTP requests)"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Route53 zone ID of the ALB (for alias records if needed)"
  value       = aws_lb.main.zone_id
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing the web service image"
  value       = aws_ecr_repository.web_service.repository_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.requests.name
}

output "s3_results_bucket" {
  description = "Name of the private S3 results bucket"
  value       = aws_s3_bucket.results.id
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic used for SMS"
  value       = aws_sns_topic.status.arn
}

output "aws_region" {
  description = "AWS region used"
  value       = var.aws_region
}

output "aws_account_id" {
  description = "Current AWS account ID (for ECR login)"
  value       = data.aws_caller_identity.current.account_id
}
