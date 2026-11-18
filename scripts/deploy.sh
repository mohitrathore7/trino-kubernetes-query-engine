#!/usr/bin/env bash
# Deploy Trino (1 coordinator + 3 workers) onto the EKS cluster created by Terraform.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$ROOT/terraform"
OVERLAY="$ROOT/k8s/overlays/eks"

tf() { terraform -chdir="$TF_DIR" output -raw "$1"; }

REGION="$(tf region)"
CLUSTER="$(tf cluster_name)"
ROLE_ARN="$(tf trino_role_arn)"

echo ">> Pointing kubectl at $CLUSTER ($REGION)"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER" >/dev/null

echo ">> Writing overlay values from terraform outputs"
cat > "$OVERLAY/generated.env" <<EOF
AWS_REGION=$REGION
EOF

cat > "$OVERLAY/generated-serviceaccount.yaml" <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: trino
  annotations:
    eks.amazonaws.com/role-arn: $ROLE_ARN
EOF

echo ">> Applying manifests"
kubectl apply -k "$OVERLAY"

echo ">> Waiting for coordinator and workers"
kubectl -n trino rollout status deploy/trino-coordinator --timeout=10m
kubectl -n trino rollout status deploy/trino-worker --timeout=10m

kubectl -n trino get pods -o wide
echo
echo "Done. Open a tunnel with:  kubectl -n trino port-forward svc/trino-coordinator 8080:8080"
