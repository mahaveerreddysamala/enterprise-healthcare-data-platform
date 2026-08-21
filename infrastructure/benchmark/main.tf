terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter { name = "name" values = ["al2023-ami-*-x86_64"] }
  filter { name = "state" values = ["available"] }
}

resource "aws_s3_bucket" "benchmark" {
  bucket = var.bucket_name
  tags = { Project = "enterprise-healthcare-data-platform", Purpose = "50m-benchmark" }
}

resource "aws_s3_bucket_public_access_block" "benchmark" {
  bucket                  = aws_s3_bucket.benchmark.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "benchmark" {
  bucket = aws_s3_bucket.benchmark.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}

resource "aws_iam_role" "benchmark" {
  name = "healthcare-benchmark-ec2-role"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}

resource "aws_iam_role_policy" "benchmark_s3" {
  role = aws_iam_role.benchmark.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["s3:ListBucket"], Resource = aws_s3_bucket.benchmark.arn }, { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "${aws_s3_bucket.benchmark.arn}/*" }] })
}

resource "aws_iam_instance_profile" "benchmark" {
  name = "healthcare-benchmark-ec2-profile"
  role = aws_iam_role.benchmark.name
}

resource "aws_security_group" "benchmark" {
  name        = "healthcare-benchmark-ec2"
  description = "Outbound-only benchmark host"
  vpc_id      = var.vpc_id
  egress { from_port = 0 to_port = 0 protocol = "-1" cidr_blocks = ["0.0.0.0/0"] }
}

resource "aws_instance" "benchmark" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.benchmark.id]
  iam_instance_profile        = aws_iam_instance_profile.benchmark.name
  associate_public_ip_address = false
  root_block_device { volume_size = var.root_volume_gb volume_type = "gp3" encrypted = true }
  user_data = file("${path.module}/user_data.sh")
  tags = { Name = "healthcare-50m-benchmark" }
}

output "bucket_name" { value = aws_s3_bucket.benchmark.bucket }
output "instance_id" { value = aws_instance.benchmark.id }
