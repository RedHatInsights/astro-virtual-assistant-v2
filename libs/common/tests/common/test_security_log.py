import base64
import json
import logging

from common.security_log import (
    get_principal_from_identity,
    log_shutdown,
    log_startup,
    security_log,
)


def _make_identity_b64(identity_dict: dict) -> str:
    return base64.b64encode(json.dumps(identity_dict).encode()).decode()


class TestGetPrincipalFromIdentity:
    def test_none_identity(self):
        result = get_principal_from_identity(None)
        assert result == {"type": "anonymous"}

    def test_user_identity(self):
        identity = _make_identity_b64(
            {
                "identity": {
                    "org_id": "org123",
                    "type": "User",
                    "user": {"user_id": "user456", "username": "testuser"},
                }
            }
        )
        result = get_principal_from_identity(identity)
        assert result == {"type": "user", "org_id": "org123", "user_id": "user456"}

    def test_service_account_identity(self):
        identity = _make_identity_b64(
            {
                "identity": {
                    "org_id": "org789",
                    "type": "ServiceAccount",
                    "service_account": {
                        "client_id": "sa-client-1",
                        "user_id": "sa-user-1",
                    },
                }
            }
        )
        result = get_principal_from_identity(identity)
        assert result == {
            "type": "service_account",
            "org_id": "org789",
            "user_id": "sa-client-1",
        }

    def test_system_identity_cert(self):
        identity = _make_identity_b64(
            {
                "identity": {
                    "org_id": "org000",
                    "type": "System",
                    "system": {"cn": "cert-cn-value"},
                }
            }
        )
        result = get_principal_from_identity(identity)
        assert result == {
            "type": "system",
            "org_id": "org000",
            "user_id": "cert-cn-value",
        }

    def test_system_identity_cluster(self):
        identity = _make_identity_b64(
            {
                "identity": {
                    "org_id": "org000",
                    "type": "System",
                    "system": {"cluster_id": "cluster-123"},
                }
            }
        )
        result = get_principal_from_identity(identity)
        assert result == {
            "type": "system",
            "org_id": "org000",
            "user_id": "cluster-123",
        }

    def test_invalid_base64(self):
        result = get_principal_from_identity("not-valid-base64!!!")
        assert result == {"type": "invalid"}

    def test_invalid_json(self):
        identity = base64.b64encode(b"not json").decode()
        result = get_principal_from_identity(identity)
        assert result == {"type": "invalid"}

    def test_missing_user_fields(self):
        identity = _make_identity_b64({"identity": {"org_id": "org123", "type": "User", "user": {}}})
        result = get_principal_from_identity(identity)
        assert result == {"type": "user", "org_id": "org123", "user_id": "unknown"}

    def test_unknown_identity_type(self):
        identity = _make_identity_b64({"identity": {"org_id": "org123", "type": "CustomType"}})
        result = get_principal_from_identity(identity)
        assert result == {
            "type": "CustomType",
            "org_id": "org123",
            "user_id": "unknown",
        }


class TestSecurityLog:
    def test_emits_log_with_required_fields(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            security_log(
                action="CREATE",
                resource_type="session",
                resource_id="sess-123",
                outcome="success",
                principal={"type": "user", "org_id": "org1", "user_id": "u1"},
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.security_event is True
        assert record.action == "CREATE"
        assert record.resource_type == "session"
        assert record.resource_id == "sess-123"
        assert record.outcome == "success"
        assert record.principal == {
            "type": "user",
            "org_id": "org1",
            "user_id": "u1",
        }

    def test_emits_log_with_reason(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            security_log(
                action="AUTH_FAILURE",
                resource_type="identity",
                resource_id="/api/test",
                outcome="failure",
                principal={"type": "anonymous"},
                reason="missing header",
            )

        record = caplog.records[0]
        assert record.reason == "missing header"

    def test_emits_log_with_service(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            security_log(
                action="STARTUP",
                resource_type="process",
                resource_id="test-service",
                outcome="success",
                principal={"type": "system"},
                service="test-service",
            )

        record = caplog.records[0]
        assert record.service == "test-service"

    def test_emits_log_with_extra_fields(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            security_log(
                action="DELETE",
                resource_type="record",
                resource_id="rec-1",
                outcome="success",
                principal={"type": "user", "org_id": "o1", "user_id": "u1"},
                custom_field="custom_value",
            )

        record = caplog.records[0]
        assert record.custom_field == "custom_value"


class TestLogStartup:
    def test_emits_startup_event(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            log_startup("my-service")

        record = caplog.records[0]
        assert record.action == "STARTUP"
        assert record.resource_type == "process"
        assert record.resource_id == "my-service"
        assert record.outcome == "success"
        assert record.principal == {"type": "system"}


class TestLogShutdown:
    def test_emits_shutdown_event(self, caplog):
        with caplog.at_level(logging.INFO, logger="security"):
            log_shutdown("my-service")

        record = caplog.records[0]
        assert record.action == "SHUTDOWN"
        assert record.resource_type == "process"
        assert record.resource_id == "my-service"
        assert record.outcome == "success"
        assert record.principal == {"type": "system"}
