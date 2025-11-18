# Hugo site Makefile - minimal targets for orthodox UNIX workflow

HUGO := hugo
HUGO_FLAGS :=
PUBLIC_DIR := public
VERIFY_SCRIPT := ../scripts/verify_html.py
ORIGINAL_DIR := ../htdocs

.PHONY: all clean dev server verify help

# Default target: build the site
all: build

# Build the site (regeneration)
build:
	@echo "Building Hugo site..."
	$(HUGO) $(HUGO_FLAGS)
	@echo "Build complete. Output in $(PUBLIC_DIR)/"

# Development server with live reload
dev: server

server:
	@echo "Starting Hugo development server..."
	@echo "Site will be available at http://localhost:1313/"
	$(HUGO) server --navigateToChanged --disableFastRender

# Clean generated files
clean:
	@echo "Cleaning $(PUBLIC_DIR)..."
	rm -rf $(PUBLIC_DIR)
	rm -f .hugo_build.lock
	@echo "Clean complete."

# Rebuild from scratch
rebuild: clean build

# Verify Hugo output matches original site
verify: build
	@echo "Verifying Hugo output against original..."
	@if [ -f $(VERIFY_SCRIPT) ]; then \
		python3 $(VERIFY_SCRIPT) $(ORIGINAL_DIR) $(PUBLIC_DIR); \
	else \
		echo "Error: Verification script not found at $(VERIFY_SCRIPT)"; \
		exit 1; \
	fi

# Verify single page (usage: make verify-page PAGE=about)
verify-page: build
	@if [ -z "$(PAGE)" ]; then \
		echo "Error: PAGE variable not set. Usage: make verify-page PAGE=about"; \
		exit 1; \
	fi
	@echo "Verifying $(PAGE).html..."
	@python3 $(VERIFY_SCRIPT) $(ORIGINAL_DIR) $(PUBLIC_DIR) $(PAGE)

# Show available targets
help:
	@echo "Available targets:"
	@echo "  make build        - Build the Hugo site (default)"
	@echo "  make dev          - Start development server with live reload"
	@echo "  make server       - Alias for dev"
	@echo "  make clean        - Remove generated files"
	@echo "  make rebuild      - Clean and build"
	@echo "  make verify       - Build and verify output matches original"
	@echo "  make verify-page PAGE=<name> - Verify single page"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make              # Build the site"
	@echo "  make dev          # Run dev server at http://localhost:1313"
	@echo "  make verify       # Verify all pages match original"
	@echo "  make verify-page PAGE=about  # Verify just about.html"
