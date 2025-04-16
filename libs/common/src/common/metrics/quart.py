import logging
import time
from typing import Callable, Optional

import quart
from quart import Quart, request, g
from quart_schema import hide
from aioprometheus import Registry, render, Counter, Histogram

QUART_EXTENSION_METRIC_REGISTRY = "metric_registry"


def register_app(app: Quart, metrics_path="/metrics"):
    registry = Registry()
    app.extensions[QUART_EXTENSION_METRIC_REGISTRY] = registry

    @app.route(metrics_path)
    @hide
    async def handle_metrics():
        content, http_headers = render(registry, request.headers.getlist("accept"))
        return content, http_headers


def get_registry(app: Quart):
    if QUART_EXTENSION_METRIC_REGISTRY not in app.extensions:
        raise KeyError(
            f"Metrics registry '{QUART_EXTENSION_METRIC_REGISTRY}' is missing. Please ensure it is registered via 'register_app'."
        )
    return app.extensions[QUART_EXTENSION_METRIC_REGISTRY]


def register_http_metrics(
    app: Quart,
    app_name: str,
    accept_paths: Optional[Callable[[quart.Request], bool]] = None,
):
    registry = get_registry(app)
    http_requests_total = Counter(
        "http_requests_total",
        "Total number of HTTP requests",
        const_labels={"app": app_name},
        registry=registry,
    )
    http_request_duration = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        const_labels={"app": app_name},
        registry=registry,
    )

    @app.before_request
    async def before():
        g.metrics_request_start_time = time.monotonic()

    @app.after_request
    async def after(response):
        if accept_paths is None or accept_paths(request):
            duration = time.monotonic() - g.metrics_request_start_time

            labels = {
                "method": request.method,
                "path": request.url_rule.rule
                if request.url_rule is not None
                else "<unknown>",
                "status": str(response.status_code),
            }

            try:
                http_requests_total.inc(labels)
                http_request_duration.observe(labels, duration)
            except Exception as e:
                logging.getLogger(__name__).error(
                    "Failed to send platform_request metrics", e
                )

        return response
