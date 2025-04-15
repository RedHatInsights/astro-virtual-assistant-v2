import time
from typing import Optional

from common.platform_request import AbstractPlatformRequest
from aioprometheus import Counter, Histogram, Registry
from aiohttp import ClientResponse

_REQUEST_TOTAL_METRIC_NAME = "platform_requests_total"
_REQUEST_DURATION_METRIC_NAME = "platform_request_duration_seconds"


class TrackedPlatformRequest(AbstractPlatformRequest):
    def __init__(
        self,
        platform_request: AbstractPlatformRequest,
        registry: Registry,
        app_name: str,
    ):
        self.request_total = (
            registry.get(_REQUEST_TOTAL_METRIC_NAME)
            if _REQUEST_TOTAL_METRIC_NAME in registry.collectors
            else Counter(
                _REQUEST_TOTAL_METRIC_NAME,
                "Total number of Platform requests",
                registry=registry,
                const_labels={"app": app_name},
            )
        )
        self.request_duration = (
            registry.get(_REQUEST_DURATION_METRIC_NAME)
            if _REQUEST_DURATION_METRIC_NAME in registry.collectors
            else Histogram(
                _REQUEST_DURATION_METRIC_NAME,
                "Duration of Platform requests in seconds",
                buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
                registry=registry,
                const_labels={"app": app_name},
            )
        )
        self.platform_request = platform_request

    async def request(
        self,
        method: str,
        base_url: str,
        api_path: str,
        user_identity: Optional[str] = None,
        **kwargs,
    ) -> ClientResponse:
        start = time.monotonic()
        status = "unknown"
        try:
            response = await self.platform_request.request(
                method, base_url, api_path, user_identity, **kwargs
            )
            status = str(response.status)
            return response
        except Exception:
            status = "exception"
            raise
        finally:
            duration = time.monotonic() - start
            labels = {
                "service": base_url,
                "method": method,
                "path": api_path,
                "status": status,
            }

            if user_identity is not None:
                labels["authenticated"] = "true"

            self.request_total.inc(labels)
            self.request_duration.observe(labels, duration)
