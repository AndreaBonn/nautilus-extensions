EXTENSIONS_DIR = $(HOME)/.local/share/nautilus-python/extensions

EXTENSIONS = \
	csv-preview/csv_preview.py \
	dockerfile-analyzer/dockerfile_analyzer.py \
	duplicate-finder/duplicate_finder.py \
	excel-preview/excel_preview.py \
	git-blame/git_blame.py \
	git-diff/git_diff.py \
	git-graph/git_graph.py \
	git-status/git_status.py \
	json-preview/json_preview.py \
	parquet-preview/parquet_preview.py \
	pdf-merger/pdf_merger.py \
	pdf-splitter/pdf_splitter.py \
	readme-viewer/readme_preview.py

.PHONY: install uninstall lint format test check restart help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all extensions to Nautilus
	@mkdir -p $(EXTENSIONS_DIR)
	@for ext in $(EXTENSIONS); do \
		cp $$ext $(EXTENSIONS_DIR)/ && \
		echo "  Installed $$(basename $$ext)"; \
	done
	@echo "\nDone. Restart Nautilus: make restart"

uninstall: ## Remove all extensions from Nautilus
	@for ext in $(EXTENSIONS); do \
		rm -f $(EXTENSIONS_DIR)/$$(basename $$ext) && \
		echo "  Removed $$(basename $$ext)"; \
	done
	@echo "\nDone. Restart Nautilus: make restart"

restart: ## Restart Nautilus
	nautilus -q 2>/dev/null; nautilus &

lint: ## Run ruff linter on all extensions
	@uv run ruff check .

format: ## Auto-format with ruff
	@uv run ruff format .

test: ## Run tests
	@uv run pytest tests/ -v

check: lint test ## Run lint + tests
