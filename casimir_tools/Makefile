# casimir-tools — build and publish commands
# Usage:
#   make build          Build wheel + sdist into dist/
#   make test           Run pytest suite
#   make publish-test   Upload to TestPyPI (dry run)
#   make publish        Upload to PyPI (real)
#   make clean          Remove build artifacts

PYTHON  ?= python
HATCH   ?= hatch
TWINE   ?= twine

.PHONY: build test publish-test publish clean

build:
	$(HATCH) build

test:
	pip install -e ".[dev]" --quiet
	pytest tests/ -v --tb=short

publish-test: build
	$(TWINE) upload --repository testpypi dist/*

publish: build test
	$(TWINE) upload dist/*
	@echo "Published casimir-tools to PyPI."

clean:
	rm -rf dist/ __pycache__ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
