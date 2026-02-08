.PHONY: test lint format install clean

test:
	python -m pytest tests/ -v --tb=short --cov=llm_integration_starter --cov-report=term-missing

lint:
	python -m ruff check .
	python -m ruff format --check .

format:
	python -m ruff format .
	python -m ruff check --fix .

install:
	pip install -e .
	pip install -r requirements-dev.txt

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
