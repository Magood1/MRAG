# Makefile for MRAG Service
.PHONY: setup run test lint security clean docker-build

PYTHON := python
VENV := .venv
BIN := $(VENV)/bin

# Environment Setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -r requirements-dev.txt
	@echo "✅ Environment setup complete. Activate with: source $(VENV)/bin/activate"

# Run Development Server
run:
	$(BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run UI Demo
run-ui:
	$(BIN)/streamlit run app/demo_ui.py

# Testing & Quality
test:
	$(BIN)/pytest -v tests/

lint:
	$(BIN)/ruff check .
	$(BIN)/black --check .

format:
	$(BIN)/black .
	$(BIN)/ruff check . --fix

# Security Audit
security-check:
	$(BIN)/bandit -r app/

# Docker Operations
docker-build:
	docker build -t mrag-service:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env mrag-service:latest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	