# Contributing to CocoMind

Thank you for your interest in contributing to CocoMind! This platform is designed as a secure, legally-defensible system for government procurement and tender evaluation. As such, we have strict quality and architectural standards.

## 🛠️ Development Setup

1. Fork and clone the repository.
2. Install the project with developer dependencies: `pip install -e ".[dev]"`
3. Set up your `.env` following `.env.example`.

## 🏗️ Code Quality Standards

We strictly enforce the following standards in our CI pipeline:

1. **Format & Lint**: We use `Ruff`. Run `ruff check src/ tests/ --fix` before committing.
2. **Types**: We employ strict static typing. Run `mypy src/` to verify.
3. **Architecture Restrictions**: The `import-linter` guarantees the pure-Python rule engine doesn't accidentally depend on LLMs. Run `lint-imports` to verify contracts.
4. **Testing**: 
   - Write standard unit tests in `pytest`.
   - Write property-based tests using `Hypothesis` for core algorithmic components.
   - Run the suite: `pytest tests/ -v`.

## 📝 Commit Guidelines

Please use semantic commit messages (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`). Keep the message scope clear:
`feat(engine): add between operator support`

## 🔒 Security Non-Negotiables

- **Never mutate data**. Prefer immutable Pydantic models.
- **Never bypass PII redaction**. All LLM interactions must go through the redacted payload interface.
- **Never write raw SQL** for modifications on the Audit chain to bypass the application layer; the triggers will block it anyway.
- **Do not commit secrets**.

## 🚦 Pull Request Process

1. Ensure all CI checks (pytest, ruff, mypy, import-linter) pass locally.
2. Ensure new features are accompanied by tests.
3. If changing architectural boundaries, explain your reasoning fully in the PR description.
4. Submit PR for review!
