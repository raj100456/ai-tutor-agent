# Contributing to Personal AI Tutor Agent

Thank you for your interest in contributing! This project is open-source under Apache 2.0.

## Quick contribution paths

The project is designed for easy extension via its plugin registries:

| What to add | Where | Complexity |
|---|---|---|
| New LLM provider | `backend/src/llm/providers/` + 1 line in `factory.py` | Low |
| New integration | `backend/src/integrations/` + `@IntegrationRegistry.register()` | Low |
| New graph node | `backend/src/graph/nodes/` + wire in `graph.py` | Medium |
| New decorator | `backend/src/graph/decorators/` + `@DecoratorRegistry.register()` | Low |
| Angular feature | `frontend/src/app/features/` | Medium |

## Development setup

```bash
# Backend
cd backend
uv sync
cp .env.example .env
uv run uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
npm install
ng serve
```

## Code style

- **Python**: `uv run ruff check src` + `uv run ruff format src`
- **TypeScript**: `ng lint`
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `docs:`, `refactor:`)

## Pull request guidelines

1. Open an issue first for non-trivial changes
2. Branch naming: `feat/`, `fix/`, `docs/`
3. Include tests for new behaviour
4. Update `config.yaml` with any new config keys and document them
5. Update the relevant section of `docs/PROJECT_OVERVIEW.md`

## Reporting bugs

Open a GitHub Issue with:
- OS and Python/Node versions
- `config.yaml` excerpt (remove secrets)
- Full error traceback
