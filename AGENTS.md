# Astro Virtual Assistant v2 — Agent Guide

## Project Overview

Astro is the virtual assistant for [console.redhat.com](https://console.redhat.com). This repo is a Python monorepo containing two services and a shared library, managed as a [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/).

### Services

| Service | Port | Purpose | API Path Prefix |
|---------|------|---------|----------------|
| **virtual-assistant** | 5000 | Public REST API — receives user messages, routes to Watson or echo assistant, returns conversation responses | `/api/virtual-assistant/v2/` |
| **watson-extension** | 5050 | Internal REST API — bridges console.redhat.com platform data for Watson conversations (advisor, notifications, RBAC, etc.) | `/api/virtual-assistant-watson-extension/v2/` |

### Shared Library

| Package | Purpose |
|---------|---------|
| **libs/common** | Auth helpers, config, identity providers, logging, metrics, platform request abstraction, session storage (Redis/file) |

## Tech Stack

- **Python** 3.12 (`.python-version`)
- **Quart** — async web framework (Flask-compatible)
- **Pydantic** v2 — request/response validation
- **injector** + **quart-injector** — dependency injection
- **aiohttp** — async HTTP client for platform requests
- **IBM Watson SDK** (`ibm-watson`, `ibm-cloud-sdk-core`) — Watson Assistant integration (virtual-assistant service only)
- **Redis** (via `redis.asyncio`) — session storage in production (Valkey 8.1.4 for local dev)
- **Hypercorn** — ASGI server for production deployments
- **uv** 0.7.22 — package manager and virtual environment
- **ruff** — linter and formatter
- **pytest** + **pytest-asyncio** — testing
- **aioresponses** — HTTP mocking for async tests
- **syrupy** — snapshot testing
- **hypothesis** — property-based testing
- **Jinja2** — response templating (watson-extension)

## Project Structure

```
astro-virtual-assistant-v2/
  deploy/clowdapp.yaml              # OpenShift ClowdApp manifest
  docker/
    Dockerfile.virtual-assistant    # Multi-stage UBI 8 build
    Dockerfile.watson-extension
  docs/                             # Human-readable documentation
  libs/
    common/                         # Shared library
      src/common/
        auth.py                     # x-rh-identity header parsing
        identity.py                 # User identity provider abstractions
        config/                     # Config helpers (python-decouple, Clowder)
        logging.py                  # CloudWatch + basic logger setup
        metrics/                    # Prometheus metrics (aioprometheus)
        platform_request/           # Abstract + concrete HTTP clients for HCC APIs
        session_storage/            # Redis, file, memory backends
        types/errors.py             # Shared error types
        providers.py                # DI provider factories
      tests/                        # Common library tests
  services/
    virtual-assistant/
      src/
        run.py                      # App entrypoint (Quart + DI wiring)
        virtual_assistant/
          config.py                 # Service config (env vars)
          startup.py                # DI bindings + route wiring
          assistant/                # Assistant abstraction (Watson, Echo)
            __init__.py             # ABC + response types (Text, Pause, Options, Command)
            watson.py               # Watson Assistant implementation
            echo.py                 # Echo assistant (dev/testing)
            response_processor/     # Post-processing pipeline (RHEL Lightspeed, CombineEmpty)
          routes/
            health.py               # GET /health/status
            talk.py                 # POST /talk — main conversation endpoint
          quart_schema.py           # OpenAPI provider customization
      tests/                        # Service tests
    watson-extension/
      src/
        run.py                      # App entrypoint
        watson_extension/
          config.py                 # Service config (env vars, service URLs)
          startup.py                # DI bindings + route wiring
          auth/                     # Auth strategies (no-auth, API key, service account)
          clients/                  # HTTP clients for HCC platform services
            insights/               # Advisor, Vulnerability, RHSM, Content Sources, Notifications
            openshift/              # OCP Advisor
            platform/               # Chrome Service, Sources, Notifications, Integrations, RBAC
            general/                # Red Hat Status
          core/                     # Business logic layer
          routes/                   # HTTP route handlers (grouped by domain)
            insights/               # /insights/advisor/*, /insights/vulnerability/*, etc.
            openshift/              # /openshift/advisor/*
            platform/               # /platform/chrome/*, /platform/notifications/*, etc.
            general/                # /general/redhat-status/*
          templates/                # Jinja2 response templates
      tests/                        # Service tests
  scripts/make/                     # Makefile modules (test, lint, variables)
```

## Architecture

### Dependency Injection

Both services use `injector` + `quart-injector` for dependency injection. The DI container is configured in each service's `startup.py`:

- **Bindings are config-driven**: session storage (Redis vs file), platform request strategy (dev vs SA vs platform), assistant type (Watson vs Echo), authentication type
- **Scopes**: `injector.singleton` for stateless services, `quart_injector.RequestScope` for per-request dependencies (identity providers, clients)
- **Providers**: factory functions in `libs/common/src/common/providers.py` create configured instances

### Authentication

**virtual-assistant**: Uses `x-rh-identity` header (base64-encoded JSON). The `@require_identity_header` decorator validates presence. Identity types: `User`, `ServiceAccount`, `System`.

**watson-extension**: Uses `x-rh-session-id` header to look up the user's identity from session storage. Additionally, incoming requests are authenticated via one of: `no-auth`, `api-key`, or `service-account` (configured via `AUTHENTICATION_TYPE`).

### Session Storage

Sessions map `session_id` to user identity (base64 `x-rh-identity`). Used to share identity between virtual-assistant and watson-extension.

- **Redis** (`SESSION_STORAGE=redis`): Production. TTL = 20 minutes. Uses `redis.asyncio`.
- **File** (`SESSION_STORAGE=file`): Local development. Stored in `.va-session-storage/`.
- **Memory**: Available but not typically used.

### Platform Requests

`AbstractPlatformRequest` provides a unified interface for calling HCC internal APIs. Three strategies:

| Mode | Config Value | Use Case |
|------|-------------|----------|
| **dev** | `PLATFORM_REQUEST=dev` | Local dev with offline token |
| **sa** | `PLATFORM_REQUEST=sa` | Service account credentials |
| **platform** | `PLATFORM_REQUEST=platform` | Production (Clowder, 3scale) |

### Watson Extension Client Pattern

Each HCC service integration follows a layered pattern:
1. **Client** (abstract + HTTP impl) — makes API calls via `AbstractPlatformRequest`
2. **Core** — business logic, transforms API responses
3. **Route** — HTTP endpoint handler, uses DI to inject client + identity
4. **Template** (Jinja2) — formats response text for the chatbot UI

API endpoint convention: `/{group}/{service}/{operation}` (e.g., `/insights/advisor/recommendations`).

### Response Types

The assistant returns typed responses via discriminated union:
- `TEXT` — plain text message
- `PAUSE` — typing indicator delay
- `OPTIONS` — button/dropdown/suggestion selection
- `COMMAND` — UI command execution

## Coding Conventions

1. **Config via env vars**: Use `python-decouple` (`config()` function). Conditional loading based on feature flags (e.g., `if console_assistant == "watson":` only then load Watson-specific vars)
2. **Async everywhere**: All route handlers, clients, and storage operations are `async`. Use `aiohttp.ClientSession` for HTTP, `redis.asyncio` for Redis
3. **Pydantic models for API contracts**: Request/response models use Pydantic v2 `BaseModel`. Validated via `@validate_request` / `@validate_response` decorators from `quart-schema`
4. **Abstract base classes**: Key abstractions (`Assistant`, `AbstractPlatformRequest`, `SessionStorage`, `Authentication`) use Python ABCs. Implementations are swapped via DI
5. **Blueprint-based routing**: Quart Blueprints organize routes hierarchically. Services register blueprints in `startup.py`'s `wire_routes()`
6. **Monorepo workspace**: `uv` workspace in `pyproject.toml` at root. Each service/lib has its own `pyproject.toml`. Cross-references use `{ workspace = true }`
7. **Conventional commits**: `type(scope): description` format. Scopes match service names: `virtual-assistant`, `watson-extension`, `common`
8. **No direct CLI calls**: Always use `make` targets or `uv run` — never call `pytest`, `ruff`, etc. directly

## Common Pitfalls

1. **Forgetting `IS_RUNNING_LOCALLY=1`**: Some config vars are required in production but optional locally. The `Makefile.variables.mk` exports this, but if running without `make`, set it manually
2. **Session storage mismatch**: virtual-assistant and watson-extension must share the same session storage backend. Watson-extension resolves user identity from session storage via `x-rh-session-id`
3. **Conditional config loading**: Config vars like `watson_api_url` only exist when `console_assistant == "watson"`. Accessing them otherwise raises `UndefinedValueError`
4. **DI scope confusion**: `singleton` vs `RequestScope` matters. Identity providers must be `RequestScope` (different user per request). Clients that hold identity providers must also be `RequestScope`
5. **Platform URL resolution**: In production, service URLs come from Clowder endpoint config (`ENDPOINT__*`). Locally, they default to `PLATFORM_URL`. Ensure the correct env vars are set for your environment
6. **Template rendering**: Watson-extension responses use Jinja2 templates. Changes to response format require updating both the template and the Pydantic response model

## Documentation Index

| Document | Description |
|----------|-------------|
| [docs/testing-guidelines.md](docs/testing-guidelines.md) | Testing patterns, fixtures, mocking strategies |
| [docs/integration-guidelines.md](docs/integration-guidelines.md) | Platform request patterns, adding new HCC service clients |
| [docs/api-guidelines.md](docs/api-guidelines.md) | API design, route conventions, request/response validation |
| [docs/index.md](docs/index.md) | High-level documentation hub |
| [docs/services/virtual-assistant.md](docs/services/virtual-assistant.md) | Virtual assistant service details |
| [docs/services/watson-extension.md](docs/services/watson-extension.md) | Watson extension service details |
| [docs/dev/how-to-configure-platform-request.md](docs/dev/how-to-configure-platform-request.md) | Platform request token setup |
| [docs/dev/proxy.md](docs/dev/proxy.md) | HTTP proxy for stage environment |
