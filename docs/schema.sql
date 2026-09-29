-- CloudOps AI — Schema v1
-- Reference DDL. Applied via Alembic migrations later (Day 8), not run directly.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin','operator','viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE infrastructure_metrics (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    container_id TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    cpu_percent REAL,
    memory_mb REAL,
    memory_percent REAL,
    network_rx_bytes BIGINT,
    network_tx_bytes BIGINT,
    replica_count INT
);
CREATE INDEX idx_infra_metrics_service_time ON infrastructure_metrics (service_name, timestamp);

CREATE TABLE application_metrics (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    request_count INT,
    latency_p50_ms REAL,
    latency_p95_ms REAL,
    latency_avg_ms REAL,
    error_count INT,
    error_rate REAL
);
CREATE INDEX idx_app_metrics_service_time ON application_metrics (service_name, timestamp);

CREATE TABLE deployments (
    id SERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    version_tag TEXT NOT NULL,
    deployed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deployed_by TEXT,
    status TEXT NOT NULL DEFAULT 'success' CHECK (status IN ('success','failed','rolled_back')),
    rollback_of INT REFERENCES deployments(id)
);

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    service_name TEXT NOT NULL,
    forecast_value REAL,
    current_value REAL,
    anomaly_detected BOOLEAN NOT NULL DEFAULT false,
    current_replicas INT,
    recommended_action TEXT NOT NULL CHECK (recommended_action IN
        ('scale_up','scale_down','no_action','self_heal')),
    confidence REAL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'recommended' CHECK (status IN
        ('recommended','approved','executed','rejected'))
);
CREATE INDEX idx_decisions_service_time ON decisions (service_name, timestamp);

CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    service_name TEXT NOT NULL,
    anomaly_type TEXT,
    severity TEXT CHECK (severity IN ('low','medium','high')),
    anomaly_score REAL,
    explanation TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX idx_incidents_service_time ON incidents (service_name, timestamp);

CREATE TABLE scaling_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    service_name TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('scale_up','scale_down','restart','rollback')),
    previous_replicas INT,
    new_replicas INT,
    trigger TEXT CHECK (trigger IN ('predictive','reactive','manual','self_heal')),
    decision_id INT REFERENCES decisions(id),
    executed_by TEXT
);
CREATE INDEX idx_scaling_events_service_time ON scaling_events (service_name, timestamp);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_service TEXT,
    details JSONB,
    result TEXT CHECK (result IN ('success','failure')),
    related_decision_id INT REFERENCES decisions(id)
);
CREATE INDEX idx_audit_log_time ON audit_log (timestamp);
