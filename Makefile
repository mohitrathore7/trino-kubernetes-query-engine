SCALE ?= sf1
RUNS  ?= 5
COMPOSE = docker compose -f docker/docker-compose.yml

.PHONY: help local-up local-load local-bench local-down \
        infra-init infra-apply infra-destroy deploy cloud-load cloud-bench \
        test lint fmt

help:          ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

# ---- Local (Docker Compose: 1 coordinator + 3 workers, MinIO, Iceberg REST) ----
local-up:      ## Start the local cluster
	$(COMPOSE) up -d --wait trino-coordinator trino-worker

local-load:    ## Load TPC-H data into Iceberg tables
	$(COMPOSE) run --rm bench load --scale $(SCALE)

local-bench:   ## Run the benchmark, results in results/benchmark.md
	$(COMPOSE) run --rm bench bench --scale $(SCALE) --runs $(RUNS)

local-down:    ## Stop and remove the local cluster
	$(COMPOSE) down -v

# ---- AWS (Terraform + EKS) ----
infra-init:    ## terraform init
	terraform -chdir=terraform init

infra-apply:   ## Provision VPC, EKS (4 nodes), S3 and Glue
	terraform -chdir=terraform apply

deploy:        ## Deploy Trino onto EKS
	./scripts/deploy.sh

cloud-load:    ## Load data on EKS (run port-forward first)
	cd python && python -m tqe load --scale $(SCALE) --schema $$(terraform -chdir=../terraform output -raw glue_database)

cloud-bench:   ## Benchmark on EKS (run port-forward first)
	cd python && python -m tqe bench --scale $(SCALE) --runs $(RUNS) --results-dir ../results \
		--schema $$(terraform -chdir=../terraform output -raw glue_database)

infra-destroy: ## Tear everything down
	kubectl delete -k k8s/overlays/eks --ignore-not-found
	terraform -chdir=terraform destroy

# ---- Dev ----
test:          ## Unit tests
	cd python && python -m pytest -q

lint:          ## Lint Python, Terraform and manifests
	cd python && ruff check . && ruff format --check .
	terraform fmt -check -recursive terraform
	kubectl kustomize k8s/base > /dev/null

fmt:           ## Auto-format
	cd python && ruff format . && ruff check --fix .
	terraform fmt -recursive terraform
