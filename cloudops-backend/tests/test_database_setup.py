"""Database configuration, metadata, and offline migration tests."""

from io import StringIO
from pathlib import Path

import app.db as db
import app.main as main_module
from alembic import command
from alembic.config import Config
from app import models
from app.core.config import Settings, settings
from fastapi.testclient import TestClient
from sqlalchemy import CheckConstraint, UniqueConstraint, make_url
from sqlalchemy.exc import SQLAlchemyError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = {
    "users": [
        "id",
        "username",
        "email",
        "hashed_password",
        "role",
        "created_at",
    ],
    "infrastructure_metrics": [
        "id",
        "service_name",
        "container_id",
        "timestamp",
        "cpu_percent",
        "memory_mb",
        "memory_percent",
        "network_rx_bytes",
        "network_tx_bytes",
        "replica_count",
    ],
    "application_metrics": [
        "id",
        "service_name",
        "timestamp",
        "request_count",
        "latency_p50_ms",
        "latency_p95_ms",
        "latency_avg_ms",
        "error_count",
        "error_rate",
    ],
    "deployments": [
        "id",
        "service_name",
        "version_tag",
        "deployed_at",
        "deployed_by",
        "status",
        "rollback_of",
    ],
    "decisions": [
        "id",
        "timestamp",
        "service_name",
        "forecast_value",
        "current_value",
        "anomaly_detected",
        "current_replicas",
        "recommended_action",
        "confidence",
        "reason",
        "status",
    ],
    "incidents": [
        "id",
        "timestamp",
        "service_name",
        "anomaly_type",
        "severity",
        "anomaly_score",
        "explanation",
        "status",
        "resolved_at",
    ],
    "scaling_events": [
        "id",
        "timestamp",
        "service_name",
        "action",
        "previous_replicas",
        "new_replicas",
        "trigger",
        "decision_id",
        "executed_by",
    ],
    "audit_log": [
        "id",
        "timestamp",
        "actor",
        "action_type",
        "target_service",
        "details",
        "result",
        "related_decision_id",
    ],
}
EXPECTED_COLUMN_TYPES = {
    "users": {
        "id": "INTEGER",
        "username": "TEXT",
        "email": "TEXT",
        "hashed_password": "TEXT",
        "role": "TEXT",
        "created_at": "TIMESTAMP WITH TIME ZONE",
    },
    "infrastructure_metrics": {
        "id": "INTEGER",
        "service_name": "TEXT",
        "container_id": "TEXT",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "cpu_percent": "REAL",
        "memory_mb": "REAL",
        "memory_percent": "REAL",
        "network_rx_bytes": "BIGINT",
        "network_tx_bytes": "BIGINT",
        "replica_count": "INTEGER",
    },
    "application_metrics": {
        "id": "INTEGER",
        "service_name": "TEXT",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "request_count": "INTEGER",
        "latency_p50_ms": "REAL",
        "latency_p95_ms": "REAL",
        "latency_avg_ms": "REAL",
        "error_count": "INTEGER",
        "error_rate": "REAL",
    },
    "deployments": {
        "id": "INTEGER",
        "service_name": "TEXT",
        "version_tag": "TEXT",
        "deployed_at": "TIMESTAMP WITH TIME ZONE",
        "deployed_by": "TEXT",
        "status": "TEXT",
        "rollback_of": "INTEGER",
    },
    "decisions": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "service_name": "TEXT",
        "forecast_value": "REAL",
        "current_value": "REAL",
        "anomaly_detected": "BOOLEAN",
        "current_replicas": "INTEGER",
        "recommended_action": "TEXT",
        "confidence": "REAL",
        "reason": "TEXT",
        "status": "TEXT",
    },
    "incidents": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "service_name": "TEXT",
        "anomaly_type": "TEXT",
        "severity": "TEXT",
        "anomaly_score": "REAL",
        "explanation": "TEXT",
        "status": "TEXT",
        "resolved_at": "TIMESTAMP WITH TIME ZONE",
    },
    "scaling_events": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "service_name": "TEXT",
        "action": "TEXT",
        "previous_replicas": "INTEGER",
        "new_replicas": "INTEGER",
        "trigger": "TEXT",
        "decision_id": "INTEGER",
        "executed_by": "TEXT",
    },
    "audit_log": {
        "id": "INTEGER",
        "timestamp": "TIMESTAMP WITH TIME ZONE",
        "actor": "TEXT",
        "action_type": "TEXT",
        "target_service": "TEXT",
        "details": "JSONB",
        "result": "TEXT",
        "related_decision_id": "INTEGER",
    },
}
REQUIRED_COLUMNS = {
    "users": {
        "id",
        "username",
        "email",
        "hashed_password",
        "role",
        "created_at",
    },
    "infrastructure_metrics": {"id", "service_name", "timestamp"},
    "application_metrics": {"id", "service_name", "timestamp"},
    "deployments": {"id", "service_name", "version_tag", "deployed_at", "status"},
    "decisions": {
        "id",
        "timestamp",
        "service_name",
        "anomaly_detected",
        "recommended_action",
        "status",
    },
    "incidents": {"id", "timestamp", "service_name", "status"},
    "scaling_events": {"id", "timestamp", "service_name", "action"},
    "audit_log": {"id", "timestamp", "actor", "action_type"},
}
EXPECTED_SERVER_DEFAULTS = {
    ("users", "role"): "'viewer'",
    ("users", "created_at"): "now()",
    ("deployments", "deployed_at"): "now()",
    ("deployments", "status"): "'success'",
    ("decisions", "timestamp"): "now()",
    ("decisions", "anomaly_detected"): "false",
    ("decisions", "status"): "'recommended'",
    ("incidents", "timestamp"): "now()",
    ("incidents", "status"): "'open'",
    ("scaling_events", "timestamp"): "now()",
    ("audit_log", "timestamp"): "now()",
}


def alembic_config(output: StringIO) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.attributes["output_buffer"] = output
    return config


def test_database_url_loads_from_environment(monkeypatch) -> None:
    expected_url = "postgresql+psycopg2://localhost:5432/cloudops_test"
    monkeypatch.setenv("DATABASE_URL", expected_url)

    configured = Settings(_env_file=None)

    assert configured.database_url == expected_url


def test_engine_uses_configured_url_without_connecting() -> None:
    assert db.engine.url == make_url(settings.database_url)
    assert db.engine.pool._pre_ping is True
    assert db.engine.pool.checkedout() == 0


def test_get_db_closes_the_session(monkeypatch) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(db, "SessionLocal", lambda: session)
    dependency = db.get_db()

    assert next(dependency) is session
    dependency.close()
    assert session.closed is True


def test_connection_probe_handles_database_errors_without_credentials(
    monkeypatch,
    caplog,
) -> None:
    class FailingEngine:
        def connect(self):
            raise SQLAlchemyError("connection failed")

    monkeypatch.setattr(db, "engine", FailingEngine())

    assert db.check_database_connection() is False
    assert "Database connection check failed" in caplog.text
    assert "connection failed" not in caplog.text


def test_database_health_endpoint_reports_connection_failures(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "check_database_connection", lambda: False)

    with TestClient(main_module.app) as client:
        response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_models_match_the_eight_documented_tables_and_columns() -> None:
    metadata = models.Base.metadata

    assert set(metadata.tables) == set(EXPECTED_COLUMNS)
    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        column_names = [column.name for column in metadata.tables[table_name].columns]
        assert column_names == expected_columns


def test_models_preserve_documented_types_nullability_and_defaults() -> None:
    from sqlalchemy.dialects import postgresql

    metadata = models.Base.metadata
    for table_name, expected_types in EXPECTED_COLUMN_TYPES.items():
        table = metadata.tables[table_name]
        assert set(table.primary_key.columns.keys()) == {"id"}
        for column_name, expected_type in expected_types.items():
            column = table.c[column_name]
            actual_type = column.type.compile(dialect=postgresql.dialect())
            assert actual_type == expected_type
            assert column.nullable is (column_name not in REQUIRED_COLUMNS[table_name])
            if column_name == "id":
                assert column.autoincrement is True

    for (table_name, column_name), expected_default in EXPECTED_SERVER_DEFAULTS.items():
        default = metadata.tables[table_name].c[column_name].server_default
        assert default is not None
        assert str(default.arg) == expected_default


def test_models_preserve_documented_constraints_and_indexes() -> None:
    metadata = models.Base.metadata
    check_names = {
        constraint.name
        for table in metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_names = {
        constraint.name
        for table in metadata.tables.values()
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    foreign_keys = {
        (
            foreign_key.parent.table.name,
            foreign_key.parent.name,
            foreign_key.target_fullname,
        )
        for table in metadata.tables.values()
        for foreign_key in table.foreign_keys
    }
    indexes = {
        index.name: (index.table.name, tuple(column.name for column in index.columns))
        for table in metadata.tables.values()
        for index in table.indexes
    }

    assert check_names == {
        "users_role_check",
        "deployments_status_check",
        "decisions_recommended_action_check",
        "decisions_status_check",
        "incidents_severity_check",
        "incidents_status_check",
        "scaling_events_action_check",
        "scaling_events_trigger_check",
        "audit_log_result_check",
    }
    assert unique_names == {"users_username_key", "users_email_key"}
    assert foreign_keys == {
        ("deployments", "rollback_of", "deployments.id"),
        ("scaling_events", "decision_id", "decisions.id"),
        ("audit_log", "related_decision_id", "decisions.id"),
    }
    assert indexes == {
        "idx_infra_metrics_service_time": (
            "infrastructure_metrics",
            ("service_name", "timestamp"),
        ),
        "idx_app_metrics_service_time": (
            "application_metrics",
            ("service_name", "timestamp"),
        ),
        "idx_decisions_service_time": ("decisions", ("service_name", "timestamp")),
        "idx_incidents_service_time": ("incidents", ("service_name", "timestamp")),
        "idx_scaling_events_service_time": (
            "scaling_events",
            ("service_name", "timestamp"),
        ),
        "idx_audit_log_time": ("audit_log", ("timestamp",)),
    }


def test_alembic_configuration_points_to_the_initial_revision() -> None:
    config = alembic_config(StringIO())

    assert config.get_main_option("script_location") == "alembic"
    assert config.get_main_option("sqlalchemy.url").endswith("/cloudops")


def test_initial_migration_generates_reversible_schema_sql() -> None:
    upgrade_output = StringIO()
    command.upgrade(alembic_config(upgrade_output), "head", sql=True)
    upgrade_sql = upgrade_output.getvalue()

    for table_name in EXPECTED_COLUMNS:
        assert f"CREATE TABLE {table_name}" in upgrade_sql
    assert "CREATE INDEX idx_infra_metrics_service_time" in upgrade_sql
    assert "CREATE INDEX idx_audit_log_time" in upgrade_sql
    assert "REFERENCES deployments (id)" in upgrade_sql
    assert "REFERENCES decisions (id)" in upgrade_sql

    downgrade_output = StringIO()
    command.downgrade(
        alembic_config(downgrade_output),
        "head:base",
        sql=True,
    )
    downgrade_sql = downgrade_output.getvalue()

    for table_name in EXPECTED_COLUMNS:
        assert f"DROP TABLE {table_name}" in downgrade_sql
