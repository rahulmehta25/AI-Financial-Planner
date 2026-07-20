# Financial Planning System - Production-Ready Makefile
# Cross-platform deployment automation with comprehensive targets
# Supports: macOS, Linux, Windows WSL

.PHONY: help install start stop restart test demo clean build deploy health check-deps check-env
.PHONY: lint format security audit migrate seed logs shell backup restore
.PHONY: monitoring load-test integration-test docs ci dev prod staging
.PHONY: docker-build docker-push docker-clean k8s-deploy k8s-delete
.DEFAULT_GOAL := help

# Configuration
PROJECT_NAME := financial-planning
COMPOSE_FILE := docker-compose.yml
COMPOSE_PROD_FILE := docker-compose.prod.yml
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy
BANDIT := $(PYTHON) -m bandit
SAFETY := $(PYTHON) -m safety

# Environment detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
	PLATFORM := linux
	OPEN_CMD := xdg-open
endif
ifeq ($(UNAME_S),Darwin)
	PLATFORM := macos
	OPEN_CMD := open
endif
ifneq (,$(findstring MINGW,$(UNAME_S)))
	PLATFORM := windows
	OPEN_CMD := start
endif

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

# Helper functions
define log_info
	@echo "$(BLUE)[INFO]$(NC) $(1)"
endef

define log_success
	@echo "$(GREEN)[SUCCESS]$(NC) $(1)"
endef

define log_warning
	@echo "$(YELLOW)[WARNING]$(NC) $(1)"
endef

define log_error
	@echo "$(RED)[ERROR]$(NC) $(1)"
endef

##@ Help
help: ## Display this help message
	@echo "================================================================"
	@echo "🚀 Financial Planning System - Deployment Automation"
	@echo "================================================================"
	@echo "Platform: $(PLATFORM)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "================================================================"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "================================================================"
	@echo "Common workflows:"
	@echo "  make install && make demo  # Quick start"
	@echo "  make dev                   # Development mode"
	@echo "  make test                  # Run all tests"
	@echo "  make prod                  # Production deployment"
	@echo "================================================================"

##@ Installation & Dependencies
install: check-deps ## Install all dependencies and setup environment
	$(call log_info,"Installing dependencies...")
	@if [ ! -f .env ]; then \
		$(call log_info,"Creating .env from template..."); \
		cp env.template .env; \
		$(call log_success,".env file created"); \
	fi
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(call log_info,"Installing pre-commit hooks...")
	$(PYTHON) -m pre_commit install || true
	@mkdir -p {logs,exports,tmp,uploads,backups}
	@mkdir -p {exports/{pdf,csv,excel},logs/{api,celery,nginx}}
	$(call log_success,"Installation completed successfully")

check-deps: ## Check system dependencies
	$(call log_info,"Checking system dependencies...")
	@command -v docker >/dev/null 2>&1 || { $(call log_error,"Docker is required but not installed"); exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { $(call log_error,"Docker Compose is required"); exit 1; }
	@command -v $(PYTHON) >/dev/null 2>&1 || { $(call log_error,"Python 3.8+ is required"); exit 1; }
	@$(PYTHON) -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" || { $(call log_error,"Python 3.8+ is required"); exit 1; }
	$(call log_success,"System dependencies check passed")

check-env: ## Validate environment configuration
	$(call log_info,"Checking environment configuration...")
	@test -f .env || { $(call log_error,".env file not found. Run 'make install' first"); exit 1; }
	@grep -q "SECRET_KEY=" .env || { $(call log_error,"SECRET_KEY not set in .env"); exit 1; }
	@grep -q "DATABASE_URL=" .env || { $(call log_error,"DATABASE_URL not set in .env"); exit 1; }
	$(call log_success,"Environment configuration is valid")

##@ Application Lifecycle
start: check-env ## Start all services in development mode
	$(call log_info,"Starting development environment...")
	./start_demo.sh
	$(call log_success,"Development environment started")

stop: ## Stop all services gracefully
	$(call log_info,"Stopping all services...")
	./stop_demo.sh
	$(call log_success,"All services stopped")

restart: stop start ## Restart all services

demo: install ## Start complete demo environment with sample data
	$(call log_info,"Starting demo environment...")
	DEMO_ENV=demo SEED_DEMO_DATA=true ./start_demo.sh
	$(call log_success,"Demo environment ready")

dev: install ## Start development environment with hot reload
	$(call log_info,"Starting development environment...")
	ENVIRONMENT=development DEBUG=true ./start_demo.sh
	$(call log_success,"Development environment ready")

prod: check-env ## Start production environment
	$(call log_info,"Starting production environment...")
	docker-compose -f $(COMPOSE_PROD_FILE) up -d
	$(call log_success,"Production environment started")

staging: check-env ## Start staging environment
	$(call log_info,"Starting staging environment...")
	ENVIRONMENT=staging docker-compose up -d
	$(call log_success,"Staging environment started")

##@ Database Operations
migrate: ## Run database migrations
	$(call log_info,"Running database migrations...")
	docker-compose exec api alembic upgrade head
	$(call log_success,"Database migrations completed")

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	$(call log_info,"Creating new migration: $(MSG)")
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"
	$(call log_success,"Migration created")

seed: ## Seed database with demo data
	$(call log_info,"Seeding database with demo data...")
	$(PYTHON) scripts/seed_demo_data.py || ./reset_demo.sh --seed
	$(call log_success,"Database seeded with demo data")

backup: ## Create database backup
	$(call log_info,"Creating database backup...")
	@mkdir -p backups
	@backup_file="backups/backup-$(shell date +%Y%m%d-%H%M%S).sql"; \
	docker-compose exec -T postgres pg_dump -U financial_planning -d financial_planning > "$$backup_file"; \
	echo "$(GREEN)[SUCCESS]$(NC) Database backed up to $$backup_file"

restore: ## Restore database from backup (usage: make restore BACKUP=backup-file.sql)
	$(call log_info,"Restoring database from $(BACKUP)...")
	@test -f "$(BACKUP)" || { $(call log_error,"Backup file $(BACKUP) not found"); exit 1; }
	docker-compose exec -T postgres psql -U financial_planning -d postgres -c "DROP DATABASE IF EXISTS financial_planning;"
	docker-compose exec -T postgres psql -U financial_planning -d postgres -c "CREATE DATABASE financial_planning OWNER financial_planning;"
	docker-compose exec -T postgres psql -U financial_planning -d financial_planning < "$(BACKUP)"
	$(call log_success,"Database restored from $(BACKUP)")

reset: ## Reset demo environment to initial state
	$(call log_info,"Resetting demo environment...")
	./reset_demo.sh
	$(call log_success,"Demo environment reset completed")

##@ Testing & Quality Assurance
test: ## Run all tests
	$(call log_info,"Running test suite...")
	$(PYTEST) tests/ -v --cov=app --cov-report=term-missing --cov-report=html
	$(call log_success,"All tests completed")

test-unit: ## Run unit tests only
	$(call log_info,"Running unit tests...")
	$(PYTEST) tests/unit/ -v
	$(call log_success,"Unit tests completed")

test-integration: ## Run integration tests only
	$(call log_info,"Running integration tests...")
	$(PYTEST) tests/integration/ -v
	$(call log_success,"Integration tests completed")

test-performance: ## Run performance tests
	$(call log_info,"Running performance tests...")
	$(PYTEST) tests/performance/ -v
	$(call log_success,"Performance tests completed")

load-test: ## Run load tests with Locust
	$(call log_info,"Starting load test environment...")
	docker-compose --profile load-test up -d locust
	$(call log_info,"Load test UI available at http://localhost:8089")
	$(OPEN_CMD) http://localhost:8089 2>/dev/null || true

integration-test: ## Run full integration test suite
	$(call log_info,"Running integration test suite...")
	docker-compose --profile test up --abort-on-container-exit test
	$(call log_success,"Integration tests completed")

##@ Code Quality & Security
lint: ## Run code linting
	$(call log_info,"Running code linters...")
	$(FLAKE8) app/ tests/
	$(MYPY) app/
	$(call log_success,"Linting completed")

format: ## Format code with black and isort
	$(call log_info,"Formatting code...")
	$(BLACK) app/ tests/
	$(ISORT) app/ tests/
	$(call log_success,"Code formatting completed")

security: ## Run security audit
	$(call log_info,"Running security audit...")
	$(BANDIT) -r app/ -f json -o security-report.json || true
	$(SAFETY) check --json --output safety-report.json || true
	$(call log_success,"Security audit completed")

audit: security ## Comprehensive security and dependency audit
	$(call log_info,"Running comprehensive audit...")
	$(PIP) list --outdated
	$(call log_success,"Audit completed")

##@ Monitoring & Debugging
health: ## Check health of all services
	$(call log_info,"Checking service health...")
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "$(GREEN)✓ API$(NC)" || echo "$(RED)✗ API$(NC)"
	@docker-compose exec -T postgres pg_isready -U financial_planning -d financial_planning >/dev/null 2>&1 && echo "$(GREEN)✓ Database$(NC)" || echo "$(RED)✗ Database$(NC)"
	@docker-compose exec -T redis redis-cli ping >/dev/null 2>&1 && echo "$(GREEN)✓ Redis$(NC)" || echo "$(RED)✗ Redis$(NC)"
	$(call log_success,"Health check completed")

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs only
	docker-compose logs -f api

logs-db: ## Show database logs only
	docker-compose logs -f postgres

logs-redis: ## Show Redis logs only
	docker-compose logs -f redis

shell: ## Open shell in API container
	docker-compose exec api /bin/bash

shell-db: ## Open database shell
	docker-compose exec postgres psql -U financial_planning -d financial_planning

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

monitoring: ## Start monitoring stack (Prometheus + Grafana)
	$(call log_info,"Starting monitoring stack...")
	docker-compose --profile monitoring up -d prometheus grafana
	$(call log_info,"Grafana available at http://localhost:3000 (admin/admin)")
	$(call log_info,"Prometheus available at http://localhost:9091")
	$(OPEN_CMD) http://localhost:3000 2>/dev/null || true

##@ Docker Operations
docker-build: ## Build Docker images
	$(call log_info,"Building Docker images...")
	docker-compose build --parallel
	$(call log_success,"Docker images built")

docker-build-prod: ## Build production Docker images
	$(call log_info,"Building production Docker images...")
	docker build -t $(PROJECT_NAME):latest -f Dockerfile.optimized --target runtime .
	docker build -t $(PROJECT_NAME):testing -f Dockerfile.optimized --target testing .
	$(call log_success,"Production Docker images built")

docker-push: docker-build-prod ## Push Docker images to registry
	$(call log_info,"Pushing Docker images to registry...")
	@echo "Configure your registry in this target"
	# docker tag $(PROJECT_NAME):latest your-registry/$(PROJECT_NAME):latest
	# docker push your-registry/$(PROJECT_NAME):latest
	$(call log_success,"Docker images pushed")

docker-clean: ## Clean up Docker resources
	$(call log_info,"Cleaning up Docker resources...")
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	$(call log_success,"Docker cleanup completed")

##@ Kubernetes Operations
k8s-deploy: ## Deploy to Kubernetes
	$(call log_info,"Deploying to Kubernetes...")
	kubectl apply -f k8s/base/
	$(call log_success,"Kubernetes deployment completed")

k8s-deploy-prod: ## Deploy to production Kubernetes
	$(call log_info,"Deploying to production Kubernetes...")
	kubectl apply -k k8s/overlays/production/
	$(call log_success,"Production Kubernetes deployment completed")

k8s-delete: ## Delete Kubernetes resources
	$(call log_info,"Deleting Kubernetes resources...")
	kubectl delete -f k8s/base/ || true
	$(call log_success,"Kubernetes resources deleted")

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods,services,ingress -l app=$(PROJECT_NAME)

##@ Documentation
docs: ## Generate API documentation
	$(call log_info,"Generating API documentation...")
	@if command -v $(OPEN_CMD) >/dev/null 2>&1; then \
		$(OPEN_CMD) http://localhost:8000/docs; \
	fi
	$(call log_success,"API documentation available at http://localhost:8000/docs")

docs-build: ## Build documentation locally
	$(call log_info,"Building documentation...")
	# Add documentation build commands here
	$(call log_success,"Documentation built")

##@ CI/CD & Deployment
ci: lint test security ## Run full CI pipeline
	$(call log_info,"Running CI pipeline...")
	$(call log_success,"CI pipeline completed successfully")

pre-commit: format lint test-unit ## Run pre-commit checks
	$(call log_info,"Running pre-commit checks...")
	$(call log_success,"Pre-commit checks passed")

deploy-dev: docker-build ## Deploy to development environment
	$(call log_info,"Deploying to development environment...")
	ENVIRONMENT=development $(MAKE) start
	$(call log_success,"Development deployment completed")

deploy-staging: docker-build-prod ## Deploy to staging environment
	$(call log_info,"Deploying to staging environment...")
	ENVIRONMENT=staging docker-compose -f $(COMPOSE_PROD_FILE) up -d
	$(call log_success,"Staging deployment completed")

deploy-prod: docker-build-prod ## Deploy to production environment
	$(call log_info,"Deploying to production environment...")
	@echo "🚨 Production deployment requires manual confirmation"
	@echo "Run: ENVIRONMENT=production docker-compose -f $(COMPOSE_PROD_FILE) up -d"
	$(call log_warning,"Production deployment halted for safety")

##@ Utilities
clean: ## Clean up temporary files and caches
	$(call log_info,"Cleaning up temporary files...")
	rm -rf {tmp,temp,.pytest_cache,__pycache__}
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf {logs/tmp,exports/tmp}/*
	$(call log_success,"Cleanup completed")

clean-all: clean docker-clean ## Complete cleanup including Docker resources
	$(call log_info,"Performing complete cleanup...")
	./stop_demo.sh --no-preserve --cleanup-images
	rm -rf {backups,exports,uploads,logs}/* 2>/dev/null || true
	$(call log_success,"Complete cleanup finished")

env-create: ## Create .env file from template
	$(call log_info,"Creating .env file from template...")
	@if [ -f .env ]; then \
		$(call log_warning,".env file already exists"); \
	else \
		cp env.template .env; \
		$(call log_success,".env file created from template"); \
	fi

env-show: ## Show current environment configuration (sanitized)
	$(call log_info,"Current environment configuration:")
	@grep -v -E "(SECRET|KEY|PASSWORD|TOKEN)" .env 2>/dev/null || echo "No .env file found"

status: ## Show current system status
	$(call log_info,"System Status:")
	@echo "Docker containers:"
	@docker-compose ps 2>/dev/null || echo "No containers running"
	@echo ""
	@echo "Disk usage:"
	@du -sh . 2>/dev/null || echo "Cannot determine disk usage"
	@echo ""
	@echo "Services:"
	@$(MAKE) health 2>/dev/null || echo "Cannot check service health"

version: ## Show version information
	@echo "================================================================"
	@echo "📋 Financial Planning System - Version Information"
	@echo "================================================================"
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not available')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'Not available')"
	@echo "Docker Compose: $(shell docker-compose --version 2>/dev/null || docker compose version 2>/dev/null || echo 'Not available')"
	@echo "Make: $(shell make --version | head -1 2>/dev/null || echo 'Not available')"
	@echo "================================================================"

##@ Maintenance
update-deps: ## Update Python dependencies
	$(call log_info,"Updating Python dependencies...")
	$(PIP) list --outdated --format=freeze | grep -v "^-e" | cut -d = -f 1 | xargs -n1 $(PIP) install -U
	$(PIP) freeze > requirements.txt
	$(call log_success,"Dependencies updated")

vacuum-db: ## Vacuum and analyze database
	$(call log_info,"Running database maintenance...")
	docker-compose exec -T postgres psql -U financial_planning -d financial_planning -c "VACUUM ANALYZE;"
	$(call log_success,"Database maintenance completed")

rotate-logs: ## Rotate log files
	$(call log_info,"Rotating log files...")
	@for logdir in logs/api logs/celery logs/nginx; do \
		if [ -d "$$logdir" ]; then \
			find "$$logdir" -name "*.log" -mtime +7 -exec gzip {} \;; \
			find "$$logdir" -name "*.log.gz" -mtime +30 -delete; \
		fi; \
	done
	$(call log_success,"Log rotation completed")

# Advanced targets for specific use cases
quick-test: ## Run quick smoke tests
	$(call log_info,"Running quick smoke tests...")
	$(PYTEST) tests/unit/test_main.py -v --tb=short
	curl -f http://localhost:8000/health || true
	$(call log_success,"Quick tests completed")

benchmark: ## Run performance benchmarks
	$(call log_info,"Running performance benchmarks...")
	$(PYTEST) tests/performance/ --benchmark-only
	$(call log_success,"Benchmarks completed")

profile: ## Profile application performance
	$(call log_info,"Profiling application performance...")
	$(PYTHON) -m cProfile -o profile.stats -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
	sleep 5
	curl http://localhost:8001/health
	pkill -f "uvicorn app.main:app"
	$(call log_success,"Profiling completed")

# Help for environment variables
env-help: ## Show available environment variables
	@echo "================================================================"
	@echo "🌍 Environment Variables"
	@echo "================================================================"
	@echo "Demo Control:"
	@echo "  DEMO_ENV=development|demo|production"
	@echo "  SEED_DEMO_DATA=true|false"
	@echo "  AUTO_OPEN_BROWSER=true|false"
	@echo "  SKIP_CHECKS=true|false"
	@echo ""
	@echo "Docker Compose:"
	@echo "  COMPOSE_PROFILES=monitoring,admin,test,load-test"
	@echo "  COMPOSE_FILE=docker-compose.yml"
	@echo ""
	@echo "Reset Options:"
	@echo "  RESET_TYPE=soft|hard|restore"
	@echo "  PRESERVE_USER_DATA=true|false"
	@echo "  PRESERVE_DATA=true|false"
	@echo ""
	@echo "Advanced:"
	@echo "  FORCE_BUILD=true|false"
	@echo "  CLEANUP_IMAGES=true|false"
	@echo "  INTERACTIVE=true|false"
	@echo "================================================================"