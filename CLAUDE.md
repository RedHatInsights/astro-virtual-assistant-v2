@AGENTS.md

## Development Commands

### Install dependencies
```bash
make install
```

### Run services
```bash
make run                    # virtual-assistant on port 5000
make run-watson-extension   # watson-extension on port 5050
make redis                  # Redis (Valkey) container for session storage
```

### Testing
```bash
make test                   # Run all tests (libs/common + both services)
make test-python-coverage   # Run tests with coverage reporting
make test-python-update-snapshot  # Update syrupy snapshots
```

Tests run per-workspace: `uv run --directory <path> pytest`. Never call `pytest` directly.

### Linting
```bash
make lint                   # Check (ruff check + ruff format --diff)
make lint-fix               # Fix (ruff check --fix + ruff format)
```

### OpenAPI
Each service auto-generates OpenAPI specs at runtime:
- virtual-assistant: `http://127.0.0.1:5000/api/virtual-assistant/v2/openapi.json`
- watson-extension: `http://127.0.0.1:5050/api/virtual-assistant-watson-extension/v2/openapi.json`

## Git Conventions

- Branch naming: `type/short-description` (e.g., `fix/session-ttl`, `feat/add-rbac-endpoint`)
- Conventional commits: `type(scope): description`
- Scopes: `virtual-assistant`, `watson-extension`, `common`, `ci`, `docs`

## Key Files

- `deploy/clowdapp.yaml` — OpenShift deployment manifest
- `services/*/src/*/config.py` — env var configuration
- `services/*/src/*/startup.py` — DI wiring and route registration
- `services/*/src/run.py` — application entrypoints
- `libs/common/src/common/providers.py` — DI provider factories
