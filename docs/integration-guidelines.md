# Integration Guidelines

## Platform Request Abstraction

All calls to HCC internal APIs go through `AbstractPlatformRequest` (in `libs/common/src/common/platform_request/`). Three implementations:

| Implementation | When | Auth Mechanism |
|---------------|------|---------------|
| `DevPlatformRequest` | Local dev (`PLATFORM_REQUEST=dev`) | Offline token → SSO refresh |
| `ServiceAccountPlatformRequest` | Service account (`PLATFORM_REQUEST=sa`) | Client credentials → SSO token |
| `PlatformRequest` | Production (`PLATFORM_REQUEST=platform`) | Forwards `x-rh-identity` header directly |

### Usage Pattern

Clients receive `AbstractPlatformRequest` via DI and call convenience methods:

```python
response = await self.platform_request.get(
    self.advisor_url,
    "/api/insights/v1/rule",
    user_identity=await self.user_identity_provider.get_user_identity(),
    params={"limit": 3},
)
```

The `user_identity` parameter is the base64-encoded `x-rh-identity` header, forwarded to downstream services for user-scoped requests.

## Adding a New HCC Service Client

Follow the existing layered pattern in watson-extension:

### 1. Define URL type

In `services/watson-extension/src/watson_extension/clients/__init__.py`:

```python
MyServiceURL = NewType("MyServiceURL", str)
```

### 2. Add config

In `services/watson-extension/src/watson_extension/config.py`:

```python
my_service_url = config("ENDPOINT__MY_SERVICE__API__URL", default=__platform_url)
```

Clowder endpoint naming: `ENDPOINT__<CLOWDAPP_NAME>__<DEPLOYMENT>__URL`.

### 3. Create client

In `services/watson-extension/src/watson_extension/clients/<group>/my_service.py`:

```python
class MyServiceClient(abc.ABC):
    @abc.abstractmethod
    async def get_data(self) -> MyData: ...

class MyServiceClientHttp(MyServiceClient):
    @injector.inject
    def __init__(
        self,
        base_url: injector.Inject[MyServiceURL],
        user_identity_provider: injector.Inject[AbstractUserIdentityProvider],
        platform_request: injector.Inject[AbstractPlatformRequest],
    ):
        self.base_url = base_url
        self.user_identity_provider = user_identity_provider
        self.platform_request = platform_request

    async def get_data(self) -> MyData:
        response = await self.platform_request.get(
            self.base_url,
            "/api/my-service/v1/data",
            user_identity=await self.user_identity_provider.get_user_identity(),
        )
        # Parse and return
```

### 4. Create core business logic

In `services/watson-extension/src/watson_extension/core/<group>/my_service.py`:

```python
class MyServiceCore:
    @injector.inject
    def __init__(self, client: injector.Inject[MyServiceClient]):
        self.client = client

    async def process(self) -> str:
        data = await self.client.get_data()
        # Transform, filter, format
        return formatted_response
```

### 5. Create route

In `services/watson-extension/src/watson_extension/routes/<group>/my_service.py`:

```python
blueprint = Blueprint("my_service", __name__, url_prefix="/my-service")

@blueprint.route("/data", methods=["GET"])
@validate_response(MyResponse, 200)
async def get_data(
    core: injector.Inject[MyServiceCore],
) -> MyResponse:
    result = await core.process()
    return MyResponse(response=result)
```

API path convention: `/{group}/{service}/{operation}` (e.g., `/insights/advisor/recommendations`).

### 6. Create Jinja2 template

In `services/watson-extension/src/watson_extension/templates/<group>/<template>.md`:

Templates format response text for the chatbot UI. They receive data from the core layer.

### 7. Wire DI bindings

In `startup.py`:
- `injector_defaults()`: bind abstract client → HTTP implementation
- `injector_from_config()`: bind URL type → config value

### 8. Register blueprint

In `startup.py`'s `wire_routes()`, register the new blueprint under the appropriate group.

### 9. Add ClowdApp dependency

In `deploy/clowdapp.yaml`, add the service to `optionalDependencies` so Clowder provides the endpoint URL.

## Session Storage

Sessions bridge virtual-assistant and watson-extension — they share the same Redis instance.

- **virtual-assistant** stores session on each `/talk` request with the user's `x-rh-identity`
- **watson-extension** resolves user identity from session via `x-rh-session-id` header
- TTL: 20 minutes (`SESSION_TTL_20_MINUTES = 1200` in `redis.py`)
- Both services must use the same `SESSION_STORAGE` backend

## Identity Resolution

| Service | Header | Identity Source |
|---------|--------|----------------|
| virtual-assistant | `x-rh-identity` | Direct from 3scale/Clowder gateway |
| watson-extension | `x-rh-session-id` | Looked up from session storage |

Watson calls the extension with the session ID. The extension resolves the original user's identity from Redis and forwards it to downstream API calls.

## Error Handling

- `AbstractPlatformRequest` returns raw `aiohttp.ClientResponse` — callers check status
- Watson SDK exceptions (`ApiException`) caught in route handlers, returned as 400 `ValidationError`
- `RequestSchemaValidationError` globally handled via `@app.errorhandler` → 400 `ValidationError`
- Downstream service failures should be handled gracefully — return user-friendly messages

## Environment Variables for Service URLs

Watson-extension uses Clowder-provided endpoint URLs:

| Env Var | Service |
|---------|---------|
| `ENDPOINT__ADVISOR_BACKEND__API__URL` | Insights Advisor |
| `ENDPOINT__RHSM_API_PROXY__SERVICE__URL` | RHSM |
| `ENDPOINT__VULNERABILITY_ENGINE__MANAGER_SERVICE__URL` | Vulnerability Engine |
| `ENDPOINT__CONTENT_SOURCES_BACKEND__SERVICE__URL` | Content Sources |
| `ENDPOINT__CCX_SMART_PROXY__SERVICE__URL` | OCP Advisor |
| `ENDPOINT__CHROME_SERVICE__API__URL` | Chrome Service |
| `ENDPOINT__SOURCES_API__SVC__URL` | Sources |
| `ENDPOINT__NOTIFICATIONS_GW__SERVICE__URL` | Notifications Gateway |
| `ENDPOINT__NOTIFICATIONS_BACKEND__SERVICE__URL` | Notifications Backend |
| `ENDPOINT__RBAC__SERVICE__URL` | RBAC |

Locally, all default to `PLATFORM_URL` (usually `https://console.redhat.com`).
