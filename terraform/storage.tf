# ---------------------------------------------------------------------------
# S3 data lake bucket that holds the Iceberg tables (Parquet files + metadata)
# ---------------------------------------------------------------------------
resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "lake" {
  bucket        = "${var.project_name}-lake-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# AWS Glue Data Catalog database used as the Iceberg catalog
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "lake" {
  name         = replace("${var.project_name}_lake", "-", "_")
  location_uri = "s3://${aws_s3_bucket.lake.bucket}/warehouse/"
}

# ---------------------------------------------------------------------------
# IAM role for the Trino service account (IRSA) - least-privilege S3 + Glue
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "trino" {
  statement {
    sid       = "ListBucket"
    actions   = ["s3:ListBucket", "s3:GetBucketLocation"]
    resources = [aws_s3_bucket.lake.arn]
  }

  statement {
    sid       = "ReadWriteObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.lake.arn}/*"]
  }

  statement {
    sid = "GlueCatalog"
    actions = [
      "glue:GetDatabase", "glue:GetDatabases",
      "glue:CreateTable", "glue:GetTable", "glue:GetTables", "glue:UpdateTable", "glue:DeleteTable",
      "glue:GetPartition", "glue:GetPartitions", "glue:BatchGetPartition",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "trino" {
  name   = "${var.project_name}-trino"
  policy = data.aws_iam_policy_document.trino.json
}

module "trino_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.44"

  role_name        = "${var.project_name}-trino"
  role_policy_arns = { trino = aws_iam_policy.trino.arn }

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["${var.trino_namespace}:${var.trino_service_account}"]
    }
  }
}
