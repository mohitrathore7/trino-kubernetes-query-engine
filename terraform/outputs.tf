output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "region" {
  description = "AWS region."
  value       = var.region
}

output "lake_bucket" {
  description = "S3 bucket that stores the Iceberg warehouse."
  value       = aws_s3_bucket.lake.bucket
}

output "glue_database" {
  description = "Glue database used as the Iceberg schema."
  value       = aws_glue_catalog_database.lake.name
}

output "trino_role_arn" {
  description = "IAM role ARN annotated on the Trino service account (IRSA)."
  value       = module.trino_irsa.iam_role_arn
}

output "kubeconfig_command" {
  description = "Run this to point kubectl at the new cluster."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
