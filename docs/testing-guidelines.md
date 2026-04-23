# Testing Guidelines

## Framework and Configuration

- **pytest** with **pytest-asyncio** (`asyncio_mode = auto`) — all async test functions and fixtures are auto-detected
- Each workspace (libs/common, services/virtual-assistant, services/watson-extension) has its own `pytest.ini`
- `pythonpath = src/` — import source modules directly without package install
- `python_classes = !TestClientProtocol` — excludes Quart's `TestClientProtocol` from test collection
- `IS_RUNNING_LOCALLY=1` set via `pytest-env` in `pytest.ini`
- Run tests: `make test` (never call `pytest` directly — use `uv run --directory <path> pytest`)

## Test Structure

Tests mirror source structure:

```
services/watson-extension/tests/
  __init__.py             # Helpers: get_resource_contents(), async_value(), get_test_template()
  app_test.py             # App-level tests
  auth/                   # Authentication strategy tests
  clients/                # HTTP client tests (aioresponses mocking)
    insights/test_advisor.py
    openshift/test_advisor.py
    test_identity.py
    test_platform_request.py
  routes/                 # Route handler tests (client mocking)
    common.py             # app_with_blueprint() helper
    insights/test_advisor.py
    platform/test_chrome.py
    ...
  resources/              # JSON fixtures for API responses
    requests/insights/advisor/categories.json
    templates/             # Expected Jinja2 template outputs
```

## Two-Level Testing Pattern

### Client Tests (integration-style)

Test HTTP clients against real API contracts using `aioresponses`:

```python
@pytest.fixture
async def aiohttp_mock():
    with aioresponses() as m:
        yield m

@pytest.fixture
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()

@pytest.fixture
async def client(session) -> AdvisorClient:
    return AdvisorClientHttp(
        AdvisorURL(""), FixedUserIdentityProvider(), PlatformRequest(session)
    )

async def test_find_rules(client, aiohttp_mock):
    aiohttp_mock.get(
        "/api/insights/v1/rule?impacting=true&rule_status=enabled&limit=3",
        status=200,
        body=get_resource_contents("requests/insights/advisor/rules_0.json"),
    )
    response = await client.find_rules()
    assert len(response.rules) == 3
```

- Mock HTTP responses with JSON from `tests/resources/requests/` files
- Use `FixedUserIdentityProvider` and `PlatformRequest(session)` for real DI wiring
- `AdvisorURL("")` — empty base URL since `aioresponses` intercepts all requests

### Route Tests (unit-style)

Test route handlers with mocked clients injected via DI:

```python
@pytest.fixture
async def advisor_client() -> MagicMock:
    return MagicMock(AdvisorClient)

@pytest.fixture
async def test_client(advisor_client) -> TestClientProtocol:
    def injector_binder(binder: injector.Binder):
        binder.bind(AdvisorClient, advisor_client)
    return app_with_blueprint(blueprint, injector_binder).test_client()

async def test_recommendations(test_client, advisor_client, snapshot):
    advisor_client.find_rules = MagicMock(
        return_value=async_value(FindRulesResponse(rules=[...], link="..."))
    )
    response = await test_client.get("/advisor/recommendations")
    assert response.status == "200 OK"
    data = await response.get_json()
    assert data["response"] == snapshot
```

- `app_with_blueprint()` from `tests/routes/common.py` creates a minimal Quart app with DI
- `MagicMock(ClientClass)` — mock the abstract client, set return values with `async_value()`
- `async_value()` helper wraps a value in a coroutine (for `MagicMock` async return values)

## Snapshot Testing

- Uses **syrupy** for snapshot comparisons of route responses
- `snapshot` fixture auto-injected by syrupy
- Update snapshots: `make test-python-update-snapshot`
- Snapshot files stored in `__snapshots__/` directories adjacent to test files

## Test Helpers

Located in `tests/__init__.py` of each service:

| Helper | Purpose |
|--------|---------|
| `get_resource_contents(path)` | Read JSON fixture file from `tests/resources/` |
| `path_to_resource(path)` | Get absolute path to resource file |
| `async_value(value)` | Wrap value in async coroutine (for MagicMock returns) |
| `get_test_template(name)` | Read expected template output from `tests/resources/templates/` |

## Writing New Tests

1. **Client test**: Add JSON response fixture to `tests/resources/requests/`, use `aioresponses` to mock the HTTP call, assert parsed response
2. **Route test**: `MagicMock` the client, use `app_with_blueprint()` for test app, assert HTTP status + response body (use `snapshot` for complex responses)
3. **Auth test**: Test authentication strategies independently with mocked requests
4. **Common lib test**: Tests in `libs/common/tests/` — test config, auth, metrics, session storage independently

## Checklist

- [ ] All tests are async functions (no `@pytest.mark.asyncio` needed — `asyncio_mode = auto`)
- [ ] Fixtures use `async` and clean up resources (e.g., `await session.close()`)
- [ ] Client tests mock HTTP, not business logic
- [ ] Route tests mock clients, not HTTP
- [ ] New JSON fixtures match real API response schemas
- [ ] Snapshot tests updated when response format changes
- [ ] Tests pass locally: `make test`
