.ONESHELL:

# =======================
# Variables
# =======================
VENV := venv
IMAGE_NAME := venkateshtangaraj/restapi
IMAGE_VERSION := v1.0.0
DOCKER_NETWORK := dem
MIGRATION_SERVICE=migration

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

CHECK_MIGRATIONS_QUERY := "SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'students') THEN 'Schema exists' ELSE 'Schema does not exist' END AS schema_status;"

# =======================
# Default target
all: run-api

# =======================
# Virtual environment setup
# =======================
install:
ifeq ($(OS),Windows_NT)
	python -m venv $(VENV)
	. $(VENV)\Scripts\Activate.ps1; 
	$(VENV)\Scripts\python -m pip install --upgrade pip; 
	$(VENV)\Scripts\pip install -r requirements.txt
else
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate; \
	$(VENV)/bin/pip install --upgrade pip; \
	$(VENV)/bin/pip install -r requirements.txt
endif

# =======================
# Database handling
# =======================
check-db:
	@echo "Checking if PostgreSQL is running..."
ifeq ($(OS),Windows_NT)
	@powershell -Command "if (docker-compose ps -q $(POSTGRES_HOST)) { Write-Host 'Database is already running' } else { Write-Host 'Database is not running' }"
else
	@if [ -n "$$(docker-compose ps -q $(POSTGRES_HOST))" ]; then \
		echo "Database is already running"; \
	else \
		echo "Database is not running"; \
	fi
endif

start-db:
	@echo "Ensuring PostgreSQL is running..."
ifeq ($(OS),Windows_NT)
	@powershell -Command "if (-not (docker-compose ps -q $(POSTGRES_HOST))) { Write-Host 'Starting PostgreSQL...'; docker-compose up $(POSTGRES_HOST) -d --wait; Write-Host 'PostgreSQL started' } else { Write-Host 'PostgreSQL already running' }"
else
	@if [ -z "$$(docker-compose ps -q $(POSTGRES_HOST))" ]; then \
		echo "Starting PostgreSQL..."; \
		docker-compose up $(POSTGRES_HOST) -d --wait; \
		echo " PostgreSQL started"; \
	else \
		echo " PostgreSQL already running"; \
	fi
endif

Code_linting:install
ifeq ($(OS),Windows_NT)
	$(VENV)\Scripts\python -m flake8 code
	$(VENV)\Scripts\python -m flake8 test
else
	$(VENV)/bin/python -m flake8 code/
	$(VENV)/bin/python -m flake8 test/
endif


check-migrations: 
	@echo "Checking if migrations are already applied..."
ifeq ($(OS),Windows_NT)
	@powershell -Command "$$result = docker-compose exec -T $(POSTGRES_HOST) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -t -c \"$(CHECK_MIGRATIONS_QUERY)\"; if ($$result -match 'Schema exists') { Write-Host 'Schema already exists' } else { Write-Host 'Schema does not exist' }"
else
	@result=$$(docker-compose exec -T $(POSTGRES_HOST) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -t -c $(CHECK_MIGRATIONS_QUERY)); \
	if echo "$$result" | grep -q "Schema exists"; then \
		echo "Schema already exists"; \
	else \
		echo "Schema does not exist"; \
	fi
endif

apply-migrations:
	@echo "Running migrations..."
	docker-compose up $(MIGRATION_SERVICE) -d	
	@echo "Migrations completed successfully."

# =======================
# API handling
# =======================
build-api:
	@echo "Building Docker image for API..."
	docker build -t $(IMAGE_NAME):$(IMAGE_VERSION) .
	@echo "Docker image $(IMAGE_NAME):$(IMAGE_VERSION) built"

run-api: start-db apply-migrations
	@echo "Starting REST API container..."
	docker-compose up restapi -d
	@echo "REST API container started"

# =======================
# Utility
# =======================
down:
	@echo "Stopping and removing containers..."
	docker-compose down

clean:
	@echo "Cleaning up..."
ifeq ($(OS),Windows_NT)
	@powershell -Command "Get-ChildItem -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -Recurse -Directory -Filter 'data' | Remove-Item -Recurse -Force"
	@powershell -Command "Get-ChildItem -Recurse -Directory -Filter 'venv' | Remove-Item -Recurse -Force"
else
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "data" -exec rm -rf {} +
	find . -type d -name "venv" -exec rm -rf {} +
endif

test:install
ifeq ($(OS),Windows_NT)
	$(VENV)\Scripts\python ./test/test.py
else
	$(VENV)/bin/python ./test/test.py
endif

.PHONY: all install check-db start-db check-migrations apply-migrations build-api run-api test down clean
