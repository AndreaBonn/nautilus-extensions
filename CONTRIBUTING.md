# Contributing to Nautilus Extensions

**Language:** [Italiano](CONTRIBUTING_IT.md) | **English**

## How to Contribute

### Reporting Bugs

Please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your system information (OS, Nautilus version, Python version)

### Suggesting Features

Open an issue describing:
- The feature you'd like to see
- Why it would be useful
- How it might work

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/AndreaBonn/nautilus-extensions.git
cd nautilus-extensions

# Install dependencies (including dev tools)
uv sync --all-extras

# Verify everything works
make check
```

### Available Commands

```bash
make lint       # Run ruff linter
make format     # Auto-format code with ruff
make test       # Run test suite
make security   # Run security checks (ruff-S + bandit + pip-audit)
make check      # Run lint + tests + security
make install    # Install extensions to Nautilus
make restart    # Restart Nautilus to pick up changes
```

## Submitting Code

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run `make check` — all lint and tests must pass
5. Commit with clear messages following the format: `type(scope): description`
   - Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`
6. Push to your fork (`git push origin feature/your-feature`)
7. Open a Pull Request

### Code Style

- Code is linted and formatted with [ruff](https://docs.astral.sh/ruff/) — run `make lint` before committing
- Use type annotations on all function parameters and return types
- Escape all GTK markup strings with `GLib.markup_escape_text()`
- All `subprocess` calls must use list-form arguments (never `shell=True`)

### Architecture Note

Each Nautilus extension **must be a single `.py` file** — this is a Nautilus constraint, not a design choice. The file is copied directly to `~/.local/share/nautilus-python/extensions/`. This means some utility functions (e.g. `fmt_size`) are duplicated across extensions by necessity.

### Testing

Every new function or bug fix must include corresponding tests:

```bash
uv run pytest tests/ -v          # Run all tests
uv run pytest tests/test_X.py -v # Run specific test file
```

- Tests live in `tests/` mirroring the extension structure
- Use behavioral assertions (test what the function does, not just that it runs)
- Name tests: `test_<function>_<scenario>_<expected_result>`

## Questions?

Open an issue for any questions.
