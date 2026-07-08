.PHONY: install backend frontend test benchmark lint format docker docs clean

# Install dependencies using uv
install:
	uv sync

# Run the backend server
backend:
	cd apps/backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run the frontend server
frontend:
	cd apps/frontend && uv run streamlit run app.py --server.port 8501

# Run unit and integration tests
test:
	cd apps/backend && PYTHONPATH=../../ uv run pytest ../../tests/ -v

# Run the E2E benchmarking and validation framework
benchmark:
	cd apps/backend && PYTHONPATH=../../ uv run python ../../evaluation/e2e/run_all.py

# Lint the codebase
lint:
	uv run ruff check .

# Format the codebase
format:
	uv run ruff format .

# Start infrastructure via Docker
docker:
	docker-compose up -d

# Generate or serve documentation
docs:
	@echo "Documentation is available in the docs/ folder."
	@echo "Markdown files can be read directly or served via mkdocs if configured."

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
