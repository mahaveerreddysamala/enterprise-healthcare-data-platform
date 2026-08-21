output "bucket_name" { value = aws_s3_bucket.benchmark.bucket }
output "instance_id" { value = aws_instance.benchmark.id }
output "region" { value = var.aws_region }
