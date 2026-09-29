# Database Schema v1

## Entity-Relationship Diagram
```mermaid
erDiagram
    DECISIONS ||--o{ SCALING_EVENTS : triggers
    DECISIONS ||--o{ AUDIT_LOG : "related to"
    DEPLOYMENTS ||--o{ DEPLOYMENTS : "rollback of"

    USERS {
        int id PK
        text username
        text email
        text hashed_password
        text role
        timestamptz created_at
    }
    INFRASTRUCTURE_METRICS {
        int id PK
        text service_name
        text container_id
        timestamptz timestamp
        float cpu_percent
        float memory_mb
        float memory_percent
        bigint network_rx_bytes
        bigint network_tx_bytes
        int replica_count
    }
    APPLICATION_METRICS {
        int id PK
        text service_name
        timestamptz timestamp
        int request_count
        float latency_p50_ms
        float latency_p95_ms
        float latency_avg_ms
        int error_count
        float error_rate
    }
    INCIDENTS {
        int id PK
        timestamptz timestamp
        text service_name
        text anomaly_type
        text severity
        float anomaly_score
        text explanation
        text status
        timestamptz resolved_at
    }
    DEPLOYMENTS {
        int id PK
        text service_name
        text version_tag
        timestamptz deployed_at
        text deployed_by
        text status
        int rollback_of FK
    }
    DECISIONS {
        int id PK
        timestamptz timestamp
        text service_name
        float forecast_value
        float current_value
        bool anomaly_detected
        int current_replicas
        text recommended_action
        float confidence
        text reason
        text status
    }
    SCALING_EVENTS {
        int id PK
        timestamptz timestamp
        text service_name
        text action
        int previous_replicas
        int new_replicas
        text trigger
        int decision_id FK
        text executed_by
    }
    AUDIT_LOG {
        int id PK
        timestamptz timestamp
        text actor
        text action_type
        text target_service
        jsonb details
        text result
        int related_decision_id FK
    }
```

## Table Purpose (one line each)
- **users** — auth + role for RBAC (P0: role column exists; enforcement is P1)
- **infrastructure_metrics** — container/host-level data from cAdvisor/node-exporter
- **application_metrics** — request rate/latency/error-rate from target-service
- **decisions** — every decision-engine cycle output, not just executed ones (needed to evaluate confidence calibration later)
- **incidents** — anomaly detector output, one row per detected anomaly
- **deployments** — CI/CD deploy history, self-referencing for rollback tracking
- **scaling_events** — only *executed* scaling actions (subset of decisions with status=executed)
- **audit_log** — every automated/manual action, source of truth for accountability
