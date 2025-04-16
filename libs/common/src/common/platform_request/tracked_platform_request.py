import logging
import time
from typing import Optional

from common.metrics import get_or_create_metric
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
        self.request_total = get_or_create_metric(
            registry,
            _REQUEST_TOTAL_METRIC_NAME,
            Counter,
            "Total number of Platform requests",
            const_labels={"app": app_name},
        )

        self.request_duration = get_or_create_metric(
            registry,
            _REQUEST_DURATION_METRIC_NAME,
            Histogram,
            "Duration of Platform requests in seconds",
            const_labels={"app": app_name},
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
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

            try:
                self.request_total.inc(labels)
                self.request_duration.observe(labels, duration)
            except Exception as e:
                logging.getLogger(__name__).error(
                    "Failed to send platform_request metrics", e
                )
