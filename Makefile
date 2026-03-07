.PHONY: install test audit score example clean help

# Default target
help:
	@echo "Agent Reliability Toolkit - Available Commands"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run all tests (requires AGENT_ENDPOINT)"
	@echo "  make audit      - Run full audit suite"
	@echo "  make score      - Generate score report from latest results"
	@echo "  make example    - Run the example echo agent"
	@echo "  make clean      - Clean up test results and cache"
	@echo ""
	@echo "Environment Variables:"
	@echo "  AGENT_ENDPOINT - Agent API endpoint (default: http://localhost:8000)"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make example &  # Start example agent in background"
	@echo "  make audit AGENT_ENDPOINT=http://localhost:8000"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Installation complete"

# Run all tests
test:
	@echo "Running test suite..."
	@if [ -z "$$AGENT_ENDPOINT" ]; then \
		echo "Error: AGENT_ENDPOINT not set"; \
		echo "Usage: make test AGENT_ENDPOINT=http://localhost:8000"; \
		exit 1; \
	fi
	pytest tests/ -v

# Run full audit
audit:
	@echo "Running full audit..."
	@if [ -z "$$AGENT_ENDPOINT" ]; then \
		echo "Error: AGENT_ENDPOINT not set"; \
		echo "Usage: make audit AGENT_ENDPOINT=http://localhost:8000"; \
		exit 1; \
	fi
	./scripts/run-audit.sh --endpoint $$AGENT_ENDPOINT

# Generate score report
score:
	@echo "Generating score report..."
	@if [ -z "$$RESULTS_FILE" ]; then \
		LATEST=$$(ls -t results/*.json 2>/dev/null | head -1); \
		if [ -z "$$LATEST" ]; then \
			echo "Error: No results files found in results/"; \
			echo "Run 'make audit' first"; \
			exit 1; \
		fi; \
		python scripts/score-agent.py $$LATEST; \
	else \
		python scripts/score-agent.py $$RESULTS_FILE; \
	fi

# Run example echo agent
example:
	@echo "Starting example echo agent..."
	@echo "Press Ctrl+C to stop"
	@echo ""
	python examples/simple-echo-agent/agent.py

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf tests/__pycache__
	rm -rf scripts/__pycache__
	rm -rf examples/simple-echo-agent/__pycache__
	rm -rf results/temp
	@echo "✓ Cleanup complete"

# Development helpers
dev-install:
	pip install -e .
	pip install pytest-watch black flake8

watch-tests:
	pytest-watch tests/ -- -v

format:
	black tests/ scripts/ examples/

lint:
	flake8 tests/ scripts/ examples/
