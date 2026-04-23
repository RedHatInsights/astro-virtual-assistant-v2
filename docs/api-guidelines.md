# API Guidelines

## Route Design

### URL Convention

Watson-extension routes follow: `/{group}/{service}/{operation}`

| Group | Service | Example |
|-------|---------|---------|
| `insights` | advisor, vulnerability, rhsm, content_sources, notifications | `/insights/advisor/recommendations` |
| `openshift` | advisor | `/openshift/advisor/recommendations` |
| `platform` | chrome, notifications, integrations, rbac | `/platform/notifications/preferences` |
| `general` | redhat_status | `/general/redhat-status/incidents` |

### Blueprint Hierarchy

```
public_root (prefix: /api/virtual-assistant-watson-extension/v2/)
  ├── insights (prefix: /insights)
  │   ├── advisor (prefix: /advisor)
  │   ├── vulnerability (prefix: /vulnerability)
  │   └── ...
  ├── platform (prefix: /platform)
  ├── openshift (prefix: /openshift)
  └── general (prefix: /general)
private_root (prefix: /)
  └── health (prefix: /health)
```

Group endpoints under the most appropriate group and service. If an endpoint queries multiple services, use the one most relevant to the operation's end goal.

## Request/Response Validation

Use `quart-schema` decorators with Pydantic v2 models:

```python
from quart_schema import validate_request, validate_response
from pydantic import BaseModel

class MyRequest(BaseModel):
    query: str
    limit: int = 10

class MyResponse(BaseModel):
    response: str

@blueprint.route("/data", methods=["POST"])
@validate_request(MyRequest)
@validate_response(MyResponse, 200)
async def get_data(data: MyRequest) -> MyResponse:
    ...
```

- Request models: `validate_request` parses and validates JSON body
- Response models: `validate_response` serializes the return value
- Validation errors are caught globally and returned as 400 `ValidationError`

## Response Format

All watson-extension endpoints return a `response` field containing a string:

```json
{
  "response": "Here are your top recommendations from Advisor:\n 1. ..."
}
```

Additional top-level attributes may be included. Nested attributes are not supported by Watsonx Assistant UI — only top-level attributes can be used.

### Virtual Assistant Response Types

The virtual-assistant service returns structured responses via a discriminated union:

| Type | Purpose | Key Fields |
|------|---------|------------|
| `TEXT` | Display text | `text: str` |
| `PAUSE` | Typing indicator | `time: int` (ms), `is_typing: bool` |
| `OPTIONS` | Selection (buttons/dropdown/suggestion) | `options: List[ResponseOption]`, `options_type` |
| `COMMAND` | UI command execution | `command: str`, `args: List` |

Response type is determined by the `type` discriminator field.

## Authentication

### Virtual Assistant (Public API)

```python
@blueprint.route("", methods=["POST"])
@require_identity_header    # Validates x-rh-identity presence
@validate_request(TalkRequest)
async def talk(data: TalkRequest, ...):
    identity = request.headers.get("x-rh-identity")
```

### Watson Extension (Internal API)

Authentication is applied globally via `@public_root.before_request`:

```python
@public_root.before_request
async def authentication_check(authentication: injector.Inject[Authentication]):
    await authentication.check_auth(quart.request)
```

Three strategies (configured via `AUTHENTICATION_TYPE`):
- `no-auth` — no authentication (local dev)
- `api-key` — validates `x-api-key` header against `API_KEYS` list
- `service-account` — validates `x-rh-identity` for matching service account `SA_CLIENT_ID`

## Dependency Injection in Routes

Route handler parameters are injected by `quart-injector`:

```python
async def talk(
    data: TalkRequest,                                         # From @validate_request
    assistant: injector.Inject[Assistant],                     # DI: singleton or request-scoped
    session_storage: injector.Inject[SessionStorage],          # DI: singleton
    processors: injector.Inject[List[ResponseProcessor]],      # DI: multi-binding
) -> TalkResponse:
```

Use `injector.Inject[Type]` type hints. The DI container resolves bindings from `startup.py`.

## OpenAPI

Both services auto-generate OpenAPI specs at runtime via `quart-schema`:

- Custom OpenAPI providers: `VirtualAssistantOpenAPIProvider`, `WatsonExtensionAPIProvider`
- Served at: `{base_url}/openapi.json`
- Interactive docs: `/redocs`, `/scalar`, `/docs` (Swagger)
- Server definitions include prod (`console.redhat.com`), stage, and local dev

## Health Checks

Both services expose `GET /health/status`:

```python
@blueprint.route("/status")
async def status() -> dict:
    return {"status": "ok"}
```

Used by Kubernetes liveness and readiness probes (configured in `deploy/clowdapp.yaml`).

## Error Handling

- `RequestSchemaValidationError` → 400 `ValidationError` (global handler in `run.py`)
- `werkzeug.exceptions.BadRequest` → 400 (raised for invalid sessions, missing headers)
- `ibm_cloud_sdk_core.ApiException` → 400 `ValidationError` (caught in talk route)
- Downstream service errors should be caught and returned as user-friendly messages
