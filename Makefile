.PHONY: install test audit score adversarial report full-audit example clean help

# Default target
help:
	@echo "Agent Reliability Toolkit - Available Commands"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run all tests (requires AGENT_ENDPOINT)"
	@echo "  make audit         - Run full audit suite"
	@echo "  make adversarial   - Run adversarial / red-team testing"
	@echo "  make report        - Generate Markdown + HTML report from latest results"
	@echo "  make full-audit    - audit + adversarial + report in one shot"
	@echo "  make score         - Generate score report from latest results"
	@echo "  make example       - Run the example echo agent"
	@echo "  make clean         - Clean up test results and cache"
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

# Run adversarial / red-team testing
adversarial:
	@echo "Running adversarial tests..."
	@if [ -z "$$AGENT_ENDPOINT" ]; then \
		echo "Error: AGENT_ENDPOINT not set"; \
		echo "Usage: make adversarial AGENT_ENDPOINT=http://localhost:8000"; \
		exit 1; \
	fi
	@AGENT=$${AGENT_NAME:-unnamed-agent}; \
	mkdir -p results; \
	python scripts/adversarial-tester.py \
		--agent "$$AGENT" \
		--endpoint $$AGENT_ENDPOINT \
		--output results/adversarial-results.json

# Generate Markdown + HTML report from latest JSON results
report:
	@echo "Generating audit report..."
	@mkdir -p reports
	@if [ -n "$$RESULTS_FILE" ]; then \
		INPUT=$$RESULTS_FILE; \
	else \
		INPUT=$$(ls -t results/*.json 2>/dev/null | head -1); \
		if [ -z "$$INPUT" ]; then \
			echo "Error: No results files found in results/"; \
			echo "Run 'make audit' or 'make adversarial' first, or set RESULTS_FILE=<path>"; \
			exit 1; \
		fi; \
	fi; \
	AGENT=$${AGENT_NAME:-unnamed-agent}; \
	python scripts/audit-report-generator.py \
		--input "$$INPUT" \
		--agent "$$AGENT" \
		--output-dir reports/ \
		--format both

# Run full audit + adversarial + report
full-audit:
	@echo "Running full audit pipeline..."
	@if [ -z "$$AGENT_ENDPOINT" ]; then \
		echo "Error: AGENT_ENDPOINT not set"; \
		echo "Usage: make full-audit AGENT_ENDPOINT=http://localhost:8000 AGENT_NAME=my-agent"; \
		exit 1; \
	fi
	@AGENT=$${AGENT_NAME:-unnamed-agent}; \
	mkdir -p results reports; \
	echo "Step 1/3: Running standard audit..."; \
	./scripts/run-audit.sh --endpoint $$AGENT_ENDPOINT || true; \
	echo "Step 2/3: Running adversarial tests..."; \
	python scripts/adversarial-tester.py \
		--agent "$$AGENT" \
		--endpoint $$AGENT_ENDPOINT \
		--output results/adversarial-results.json || true; \
	echo "Step 3/3: Generating report..."; \
	LATEST=$$(ls -t results/*.json 2>/dev/null | head -1); \
	if [ -n "$$LATEST" ]; then \
		python scripts/audit-report-generator.py \
			--input "$$LATEST" \
			--agent "$$AGENT" \
			--output-dir reports/ \
			--format both; \
	fi; \
	echo ""; \
	echo "Full audit complete. Reports in reports/"

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
