# System Architecture

```mermaid
flowchart TB
    Locust["Locust\n(traffic generator)"] --> TS["Target Service\n(FastAPI, instrumented)"]
    TS -- "/metrics" --> Prom["Prometheus"]
    CAdv["cAdvisor / node-exporter"] --> Prom
    Prom --> Graf["Grafana\n(ops dashboards)"]
    Prom --> Worker["Metrics-Ingestion Worker\n(APScheduler, 30s poll)"]
    Worker --> DB[("PostgreSQL\ninfra/app metrics, incidents,\ndeployments, scaling_events,\ndecisions, audit_log, users")]

    DB --> Fore["ML Forecaster\n(XGBoost)"]
    DB --> Anom["Anomaly Detector\n(Isolation Forest)"]
    DB --> Cost["Cost Engine"]

    Fore --> Dec["Decision Engine"]
    Anom --> Dec
    Cost --> Dec

    Dec -- "recommendation mode" --> DB
    Dec -- "automatic mode" --> Exec["Action Executor\n(allowlisted)"]
    Exec --> Compose["docker compose scale N"]
    Exec --> ECS["ECS update_service\n(P1 stretch)"]
    Exec --> Heal["restart / replace container\n/ rollback deployment"]
    Exec --> Audit[("audit_log")]

    Backend["CloudOps Backend API\n(FastAPI)"] <--> DB
    Backend <--> Dash["React Dashboard"]

    GHA["GitHub Actions"] -- "push -> lint+test -> build -> push image" --> Deploy["Deploy to EC2 / ECS"]
```

## Module Responsibilities (summary — full detail in `module-boundaries.md`)

- **target-service** — the monitored application; exposes business endpoints + `/metrics`
- **cloudops-backend** — control plane: API, DB access, ML inference, decision engine, action executor
- **ml** — offline training pipeline; produces serialized models consumed by cloudops-backend
- **dashboard** — React frontend, talks only to cloudops-backend's API
- **infra** — Docker Compose, Prometheus/Grafana config, deployment scripts
