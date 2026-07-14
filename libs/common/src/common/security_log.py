"""SEC-MON-REQ-1 security logging module.

Provides structured security event logging with required fields:
- action: The operation being performed (CREATE, READ, UPDATE, DELETE, or custom)
- resource_type: Type of resource being operated on
- resource_id: Identifier of the specific resource
- outcome: 'success' or 'failure'
- principal: Identity performing the action (org_id, user_id, type)
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

logger = logging.getLogger("security")


def get_principal_from_identity(identity_b64: str | None) -> dict[str, Any]:
    """Extract principal information from a base64-encoded x-rh-identity header.

    Returns a dict with org_id, user_id, and type fields.
    """
    if not identity_b64:
        return {"type": "anonymous"}

    try:
        decoded = json.loads(base64.b64decode(identity_b64).decode("utf-8"))
        identity = decoded.get("identity", {})
        org_id = identity.get("org_id", "unknown")
        identity_type = identity.get("type", "unknown")

        if identity_type == "User":
            user = identity.get("user", {})
            return {
                "type": "user",
                "org_id": org_id,
                "user_id": user.get("user_id", "unknown"),
            }
        elif identity_type == "ServiceAccount":
            sa = identity.get("service_account", {})
            return {
                "type": "service_account",
                "org_id": org_id,
                "user_id": sa.get("client_id", sa.get("user_id", "unknown")),
            }
        elif identity_type == "System":
            system = identity.get("system", {})
            return {
                "type": "system",
                "org_id": org_id,
                "user_id": system.get("cn", system.get("cluster_id", "unknown")),
            }
        else:
            return {"type": identity_type, "org_id": org_id, "user_id": "unknown"}
    except Exception:
        return {"type": "invalid"}


def security_log(
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    outcome: str,
    principal: dict[str, Any],
    reason: str | None = None,
    service: str | None = None,
    **extra: Any,
) -> None:
    """Emit a structured security event log entry.

    All security logs include a `security_event: true` marker for filtering
    in log aggregation systems.
    """
    log_data: dict[str, Any] = {
        "security_event": True,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "principal": principal,
    }

    if reason:
        log_data["reason"] = reason

    if service:
        log_data["service"] = service

    if extra:
        log_data.update(extra)

    logger.info("security event: %(data)s", {"data": log_data}, extra=log_data)


def log_startup(service_name: str) -> None:
    """Log a process startup event (EOI-5)."""
    security_log(
        action="STARTUP",
        resource_type="process",
        resource_id=service_name,
        outcome="success",
        principal={"type": "system"},
        service=service_name,
    )


def log_shutdown(service_name: str) -> None:
    """Log a process shutdown event (EOI-5)."""
    security_log(
        action="SHUTDOWN",
        resource_type="process",
        resource_id=service_name,
        outcome="success",
        principal={"type": "system"},
        service=service_name,
    )
