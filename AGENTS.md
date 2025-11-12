# Repository Guidelines

This file documents how to work in this repository efficiently and consistently.
It includes project structure, environment setup, coding standards, and how to run
common tasks. Follow these guidelines for all changes within this repo.

## Project Structure & Module Organization

- Use this layout for any new code: `src/` (source), `tests/` (unit/integration),
  `docs/` (documentation), `assets/` (static files like models).
- Example: place a new module at `src/tooling/runner.py` and its test at
  `tests/tooling/test_runner.py`.
- Python modules live directly under `src/` (pytest adds `src/` to `PYTHONPATH` via
  `pyproject.toml`). Prefer absolute imports (`from src.module import X`) and avoid
  relative imports (enforced by Ruff config).
- The `scripts/` directory is reserved for advanced utilities only—all common tasks
  (test, lint, build, CI) are managed via `pixi run` in `pixi.toml`.

## Environment & Tooling (Pixi)

Pixi is the single source of truth for the virtual environment and tasks.
Do not rely on the system Python or `pip` outside Pixi.

- Create/update the environment from `pixi.toml` and `pixi.lock`:

  ```bash
  pixi install
  ```

- Run tasks in the managed environment:

  ```bash
  pixi run dev            # lint → test → coverage
  pixi run test           # run test suite with coverage
  pixi run lint           # ruff checks and formatting validation
  pixi run test-coverage  # detailed coverage analysis
  pixi run pre-commit     # fast staged checks before committing
  pixi run ci             # CI pipeline locally
  pixi run format         # apply ruff formatting
  pixi run security       # bandit security scan
  pixi run clean          # clean test/coverage artifacts
  pixi run main           # run the application
  pixi run cam            # camera detection test
  ```

- Optional interactive shell in the environment:

  ```bash
  pixi shell
  ```

- Adding dependencies:

  - Conda (conda-forge) packages: `pixi add opencv`.
  - PyPI packages: `pixi add --pypi onvif-zeep` or `pixi add pypi::onvif-zeep`.
  - Keep dependencies in `pixi.toml` (`[dependencies]` and `[pypi-dependencies]`).
  - Commit both `pixi.toml` and `pixi.lock` with changes.

- Prefer `pixi run <task>` for all workflows. This ensures commands run in the
  correct environment with all dependencies available. All development tasks are
  defined as Pixi tasks in `pixi.toml`.

## Build, Test, and Development Commands

- No build step is required. Use Pixi tasks for deterministic workflows.
- Common flows:
  - Local dev loop: `pixi run dev`
  - Quick tests: `pixi run test`
  - Lint/format: `pixi run lint` then `pixi run format` to apply fixes
  - CI check locally: `pixi run ci`
- Use `rg` for fast search (e.g., `rg "TODO" src tests`).

## TDD Policy

- Follow red → green → refactor: write a failing test, make it pass minimally,
  then refactor while keeping the suite green.
- Keep tests fast and deterministic; isolate network, filesystem, and external
  tools with fakes or mocks.
- Enforce a coverage floor locally and in CI; raise the floor only when stable.
  See `pyproject.toml` for coverage configuration.
- Add proper comments and/or docstrings as you go.

## Coding Style & Naming Conventions

- General: keep diffs minimal, self‑contained, and documented.
- Python: Ruff (Black‑compatible formatting + isort). 4‑space indent; `snake_case`
  for modules/functions, `PascalCase` for classes. Configuration lives in
  `pyproject.toml`.
- Imports: absolute imports only (relative imports are banned in Ruff config).
- Markdown: wrap at ~100 cols; use fenced code blocks with language hints.

## Testing Guidelines

- Place tests in `tests/` mirroring `src/` structure. Prefer `tests/unit/` and
  `tests/integration/` when useful.
- Naming: `test_*.py` for pytest.
- Quick starts:
  - Python: `pixi run test` (or `pytest -q` from `pixi shell`).
- Prefer fast, deterministic tests; include at least one smoke test per
  module.

## Commit & Pull Request Guidelines

- Use Conventional Commits when possible: `feat: add session exporter`.
- Commit messages: imperative mood, short subject (<72 chars), concise body.
- PRs: clear description, linked issues, before/after output or screenshots for
  CLI tools, and test evidence.

## Security & Configuration Tips

- Do NOT commit secrets. Treat `auth.json`, `history.jsonl`, `sessions/`, and
  `log/` as sensitive; add to `.gitignore` if versioning this folder.
- Redact tokens in examples; prefer environment variables over plaintext configs.
- Large artifacts (e.g., model weights under `models/`) should be ignored or
  retrieved at runtime if applicable.

## Agent‑Specific Instructions

- Respect this AGENTS.md across the repo scope.
- Avoid adding licenses or broad refactors unless requested. Keep one
  in‑progress plan step and summarize changes clearly.
- When working with Python code, always use the Pixi environment (`pixi run …`
  or `pixi shell`). Do not rely on the system interpreter.

## MCP

- When working with dependencies, software libraries, API, third party tools,
  etc., first check with the Context7 MCP server for the most up‑to‑date
  documentation.
- For anything needing external information (research or online data gathering),
  use the brave-search MCP server.
- If a specific URL requires accessing/scraping/crawling/extracting data, use
  the hyperbrowser MCP server.

## SOLID Principles

Five design principles that make software more maintainable, flexible, and scalable.

### Single Responsibility (SRP)

Each class should have only one reason to change, with one specific responsibility.

- Separate UI widgets from business logic
- Keep repositories focused on data operations only
- Isolate validation logic into dedicated validator classes
- Benefits: easier testing, clearer code purpose, simpler maintenance

### Open/Closed (OCP)

Software entities should be open for extension but closed for modification.

- Use abstract classes and interfaces to define contracts
- Extend functionality by creating new implementations, not modifying existing code
- Example: Create `PaymentMethod` interface, then extend with `CreditCard`, `PayPal`, etc.
- Benefits: reduces bugs in existing code, safer to add features

### Liskov Substitution (LSP)

Objects of a subclass must be substitutable for objects of their parent class.

- Subclasses should strengthen, not weaken, parent class behavior
- Don't throw exceptions in overridden methods that parent doesn't throw
- Example: If `Bird` has `move()`, all bird subclasses should implement valid movement
- Benefits: predictable behavior, safer inheritance hierarchies

### Interface Segregation (ISP)

Clients shouldn't be forced to depend on interfaces they don't use.

- Create small, focused interfaces instead of large, monolithic ones
- Split `Worker` interface into `Workable`, `Eatable`, `Sleepable`
- Classes implement only the interfaces they need
- Benefits: more flexible code, easier to implement and test

### Dependency Inversion (DIP)

Depend on abstractions, not concrete implementations.

- High-level modules shouldn't depend on low-level modules
- Use dependency injection to provide implementations
- Define abstract `DataSource`, inject `ApiClient` or `LocalDatabase`
- Benefits: easier testing with mocks, flexible architecture, decoupled code

---

## DRY Principle (Don't Repeat Yourself)

- Extract repeated UI patterns into reusable widgets
- Use Dart mixins to share functionality across classes
- Separate business logic from UI components
- Create utility functions for common operations
- Benefits: less code, easier maintenance, fewer bugs, better testing

---

## KISS Principle (Keep It Simple, Stupid)

- Use Flutter's built-in widgets instead of creating complex custom solutions
- Write self-explanatory code with clear variable/function names
- Avoid over-engineering simple problems
- Minimize external dependencies
- Break down complex widgets into smaller, manageable pieces
- Start simple, add complexity only when necessary

---

## YAGNI Principle (You Aren't Gonna Need It)

Don't implement functionality until it's actually needed.

- Resist the urge to build features "just in case" they might be useful later
- Focus on current requirements, not hypothetical future needs
- Don't create abstract layers for one implementation
- Avoid premature optimization before measuring performance
- Don't build configuration systems until you need configurability
- Wait for actual use cases before adding flexibility
- Benefits: less code to maintain, faster delivery, lower complexity, easier to change
