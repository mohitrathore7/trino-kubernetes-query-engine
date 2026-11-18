variable "project_name" {
  description = "Prefix used for all resource names."
  type        = string
  default     = "trino-query-engine"
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "kubernetes_version" {
  description = "EKS control plane version."
  type        = string
  default     = "1.30"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "coordinator_instance_type" {
  description = "Instance type for the single Trino coordinator node."
  type        = string
  default     = "m6i.xlarge"
}

variable "worker_instance_type" {
  description = "Instance type for Trino worker nodes."
  type        = string
  default     = "r6i.xlarge"
}

variable "worker_count" {
  description = "Number of Trino worker nodes (1 coordinator + N workers)."
  type        = number
  default     = 3
}

variable "trino_namespace" {
  description = "Kubernetes namespace Trino runs in (used for IRSA trust)."
  type        = string
  default     = "trino"
}

variable "trino_service_account" {
  description = "Kubernetes service account Trino pods use (used for IRSA trust)."
  type        = string
  default     = "trino"
}
