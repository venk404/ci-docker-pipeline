# CI/CD Pipeline with GitHub Actions

## Overview
This repository demonstrates a comprehensive CI/CD pipeline using GitHub Actions to automate building, testing, and deploying a FastAPI application with Docker containers.

## Pipeline Features
- 🔄 Automated builds on push and pull requests
- 📦 Python dependency caching
- ✅ Unit testing
- 🔍 Code quality checks with Flake8
- 🐳 Docker image building and publishing
- 🚀 Triggering CD pipeline

## Prerequisites
- GitHub account
- Self-hosted runner
- Docker Hub account

## Requirements
- VMs for self-hosted runner
- Docker & Docker Compose in runner machine.
- Make utility

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/venk404/ci-docker-pipeline.git
   cd ci-docker-pipeline/
   ```

2. **Build and Run**
   ```bash
   make all
   ```

## Individual Commands

### Database Operations

**Start Database**
```bash
make Start_DB
```

**Run Database Migrations**
```bash
make run-migrations
```

### API Operations

**Build API**
```bash
make build-api
```

**Run API**
```bash
make run-api
```

### Testing

**Run Tests**
```bash
make test
```

## CI Configuration

### GitHub Secrets Required
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `PAT_TOKEN`: GitHub Personal Access Token

### GitHub Variables
- `DOCKERHUB_USERNAME`: Your Docker Hub username

## Workflow Triggers
- Push to main branch
- Pull request events
- Manual workflow dispatch

## Pipeline Stages

1. **Setup & Build**
   - Python environment setup
   - Dependencies installation
   - Package caching

2. **Test & Quality**
   - Unit tests execution
   - Flake8 code linting

3. **Docker Operations**
   - Build REST API image
   - Build DB migrations image
   - Push to Docker Hub

4. **Deployment**
   - Trigger CD pipeline


## Conclusions

All the expectations have been met for **Milestone 4**:

- ✅ CI pipeline created to build and push Docker images to a central registry (DockerHub/GitHub Container Registry).  
- ✅ Pipeline stages implemented: Build API, Run tests, Code linting, Docker login, Docker build and push.  
- ✅ Appropriate Makefile targets used for building, testing, and linting.  
- ✅ CI pipeline runs on a self-hosted GitHub runner.  
- ✅ Pipeline triggered only on changes in the code directory.  
- ✅ Manual pipeline trigger supported for developers.  