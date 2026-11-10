"""SQLAlchemy models matching docs/schema.sql (Schema v1)."""

from app.db import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, REAL, TIMESTAMP


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'operator', 'viewer')",
            name="users_role_check",
        ),
        UniqueConstraint("username", name="users_username_key"),
        UniqueConstraint("email", name="users_email_key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(Text, nullable=False, server_default=text("'viewer'"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class InfrastructureMetric(Base):
    __tablename__ = "infrastructure_metrics"
    __table_args__ = (
        Index("idx_infra_metrics_service_time", "service_name", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(Text, nullable=False)
    container_id = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    cpu_percent = Column(REAL, nullable=True)
    memory_mb = Column(REAL, nullable=True)
    memory_percent = Column(REAL, nullable=True)
    network_rx_bytes = Column(BigInteger, nullable=True)
    network_tx_bytes = Column(BigInteger, nullable=True)
    replica_count = Column(Integer, nullable=True)


class ApplicationMetric(Base):
    __tablename__ = "application_metrics"
    __table_args__ = (
        Index("idx_app_metrics_service_time", "service_name", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    request_count = Column(Integer, nullable=True)
    latency_p50_ms = Column(REAL, nullable=True)
    latency_p95_ms = Column(REAL, nullable=True)
    latency_avg_ms = Column(REAL, nullable=True)
    error_count = Column(Integer, nullable=True)
    error_rate = Column(REAL, nullable=True)


class Deployment(Base):
    __tablename__ = "deployments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'rolled_back')",
            name="deployments_status_check",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(Text, nullable=False)
    version_tag = Column(Text, nullable=False)
    deployed_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    deployed_by = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default=text("'success'"))
    rollback_of = Column(
        Integer,
        ForeignKey("deployments.id", name="deployments_rollback_of_fkey"),
        nullable=True,
    )


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint(
            "recommended_action IN "
            "('scale_up', 'scale_down', 'no_action', 'self_heal')",
            name="decisions_recommended_action_check",
        ),
        CheckConstraint(
            "status IN ('recommended', 'approved', 'executed', 'rejected')",
            name="decisions_status_check",
        ),
        Index("idx_decisions_service_time", "service_name", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    service_name = Column(Text, nullable=False)
    forecast_value = Column(REAL, nullable=True)
    current_value = Column(REAL, nullable=True)
    anomaly_detected = Column(Boolean, nullable=False, server_default=text("false"))
    current_replicas = Column(Integer, nullable=True)
    recommended_action = Column(Text, nullable=False)
    confidence = Column(REAL, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default=text("'recommended'"))


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high')",
            name="incidents_severity_check",
        ),
        CheckConstraint(
            "status IN ('open', 'resolved')",
            name="incidents_status_check",
        ),
        Index("idx_incidents_service_time", "service_name", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    service_name = Column(Text, nullable=False)
    anomaly_type = Column(Text, nullable=True)
    severity = Column(Text, nullable=True)
    anomaly_score = Column(REAL, nullable=True)
    explanation = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default=text("'open'"))
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)


class ScalingEvent(Base):
    __tablename__ = "scaling_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('scale_up', 'scale_down', 'restart', 'rollback')",
            name="scaling_events_action_check",
        ),
        CheckConstraint(
            "trigger IN ('predictive', 'reactive', 'manual', 'self_heal')",
            name="scaling_events_trigger_check",
        ),
        Index("idx_scaling_events_service_time", "service_name", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    service_name = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    previous_replicas = Column(Integer, nullable=True)
    new_replicas = Column(Integer, nullable=True)
    trigger = Column(Text, nullable=True)
    decision_id = Column(
        Integer,
        ForeignKey("decisions.id", name="scaling_events_decision_id_fkey"),
        nullable=True,
    )
    executed_by = Column(Text, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(
            "result IN ('success', 'failure')",
            name="audit_log_result_check",
        ),
        Index("idx_audit_log_time", "timestamp"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    actor = Column(Text, nullable=False)
    action_type = Column(Text, nullable=False)
    target_service = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    result = Column(Text, nullable=True)
    related_decision_id = Column(
        Integer,
        ForeignKey("decisions.id", name="audit_log_related_decision_id_fkey"),
        nullable=True,
    )
