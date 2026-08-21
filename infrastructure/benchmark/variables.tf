variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name"
}

variable "vpc_id" {
  type        = string
  description = "Existing VPC ID"
}

variable "subnet_id" {
  type        = string
  description = "Private subnet ID with NAT egress"
}

variable "instance_type" {
  type    = string
  default = "m6i.2xlarge"
}

variable "root_volume_gb" {
  type    = number
  default = 150
}
