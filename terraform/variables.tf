variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "pipeline"
}

variable "phone_number" {
  description = "E.164 phone number for SNS SMS (e.g. +1234567890)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR for the new VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ecs_desired_count" {
  description = "Number of ECS tasks for Web Service"
  type        = number
  default     = 2
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for pipeline input"
  type        = string
  default     = "pipeline-requests"
}

variable "s3_results_bucket_prefix" {
  description = "Prefix for the S3 results bucket name (account/region will be used for uniqueness)"
  type        = string
  default     = "pipeline-results"
}

variable "ecr_repository_name" {
  description = "ECR repository name for web service image"
  type        = string
  default     = "pipeline-web-service"
}

variable "web_service_image_tag" {
  description = "Docker image tag for ECS service (e.g. latest)"
  type        = string
  default     = "latest"
}
