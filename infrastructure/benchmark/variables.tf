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
  description = "Existing VPC ID used for the temporary benchmark host"
}

variable "subnet_id" {
  type        = string
  description = "Existing public subnet ID with Internet Gateway egress"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size for the benchmark; keep configurable for cost/performance testing"
  default     = "m6i.xlarge"
}

variable "root_volume_gb" {
  type        = number
  description = "Encrypted gp3 root volume size in GB"
  default     = 100
}
