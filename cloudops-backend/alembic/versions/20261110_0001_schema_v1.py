"""Create the documented CloudOps AI Schema v1."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261110_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column(
            "role",
            sa.Text(),
            server_default=sa.text("'viewer'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'operator', 'viewer')",
            name="users_role_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="users_email_key"),
        sa.UniqueConstraint("username", name="users_username_key"),
    )
    op.create_table(
        "infrastructure_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("container_id", sa.Text(), nullable=True),
        sa.Column("timestamp", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("cpu_percent", postgresql.REAL(), nullable=True),
        sa.Column("memory_mb", postgresql.REAL(), nullable=True),
        sa.Column("memory_percent", postgresql.REAL(), nullable=True),
        sa.Column("network_rx_bytes", sa.BigInteger(), nullable=True),
        sa.Column("network_tx_bytes", sa.BigInteger(), nullable=True),
        sa.Column("replica_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_infra_metrics_service_time",
        "infrastructure_metrics",
        ["service_name", "timestamp"],
        unique=False,
    )
    op.create_table(
        "application_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("timestamp", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=True),
        sa.Column("latency_p50_ms", postgresql.REAL(), nullable=True),
        sa.Column("latency_p95_ms", postgresql.REAL(), nullable=True),
        sa.Column("latency_avg_ms", postgresql.REAL(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("error_rate", postgresql.REAL(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_app_metrics_service_time",
        "application_metrics",
        ["service_name", "timestamp"],
        unique=False,
    )
    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("version_tag", sa.Text(), nullable=False),
        sa.Column(
            "deployed_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deployed_by", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'success'"),
            nullable=False,
        ),
        sa.Column("rollback_of", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "status IN ('success', 'failed', 'rolled_back')",
            name="deployments_status_check",
        ),
        sa.ForeignKeyConstraint(
            ["rollback_of"],
            ["deployments.id"],
            name="deployments_rollback_of_fkey",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("forecast_value", postgresql.REAL(), nullable=True),
        sa.Column("current_value", postgresql.REAL(), nullable=True),
        sa.Column(
            "anomaly_detected",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("current_replicas", sa.Integer(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("confidence", postgresql.REAL(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'recommended'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "recommended_action IN "
            "('scale_up', 'scale_down', 'no_action', 'self_heal')",
            name="decisions_recommended_action_check",
        ),
        sa.CheckConstraint(
            "status IN ('recommended', 'approved', 'executed', 'rejected')",
            name="decisions_status_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_decisions_service_time",
        "decisions",
        ["service_name", "timestamp"],
        unique=False,
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("anomaly_type", sa.Text(), nullable=True),
        sa.Column("severity", sa.Text(), nullable=True),
        sa.Column("anomaly_score", postgresql.REAL(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'open'"),
            nullable=False,
        ),
        sa.Column("resolved_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="incidents_severity_check",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'resolved')",
            name="incidents_status_check",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_incidents_service_time",
        "incidents",
        ["service_name", "timestamp"],
        unique=False,
    )
    op.create_table(
        "scaling_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("previous_replicas", sa.Integer(), nullable=True),
        sa.Column("new_replicas", sa.Integer(), nullable=True),
        sa.Column("trigger", sa.Text(), nullable=True),
        sa.Column("decision_id", sa.Integer(), nullable=True),
        sa.Column("executed_by", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "action IN ('scale_up', 'scale_down', 'restart', 'rollback')",
            name="scaling_events_action_check",
        ),
        sa.CheckConstraint(
            "trigger IN ('predictive', 'reactive', 'manual', 'self_heal')",
            name="scaling_events_trigger_check",
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["decisions.id"],
            name="scaling_events_decision_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_scaling_events_service_time",
        "scaling_events",
        ["service_name", "timestamp"],
        unique=False,
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action_type", sa.Text(), nullable=False),
        sa.Column("target_service", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("related_decision_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "result IN ('success', 'failure')",
            name="audit_log_result_check",
        ),
        sa.ForeignKeyConstraint(
            ["related_decision_id"],
            ["decisions.id"],
            name="audit_log_related_decision_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_audit_log_time",
        "audit_log",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_audit_log_time", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("idx_scaling_events_service_time", table_name="scaling_events")
    op.drop_table("scaling_events")
    op.drop_index("idx_incidents_service_time", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("idx_decisions_service_time", table_name="decisions")
    op.drop_table("decisions")
    op.drop_table("deployments")
    op.drop_index("idx_app_metrics_service_time", table_name="application_metrics")
    op.drop_table("application_metrics")
    op.drop_index(
        "idx_infra_metrics_service_time",
        table_name="infrastructure_metrics",
    )
    op.drop_table("infrastructure_metrics")
    op.drop_table("users")
