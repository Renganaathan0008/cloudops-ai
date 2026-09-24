# CloudOps AI — Project Charter

## Objective

An intelligent cloud-native platform that monitors a real deployed service,
forecasts near-term load, detects anomalies, and recommends/executes scaling
and self-healing actions — with measured cost and performance impact versus
static and reactive baselines. Every reported number must come from real
traffic against a real deployed stack, not synthetic/mock data.

## P0 Scope (must work end-to-end)

- Target/load-simulation service (FastAPI, instrumented)
- PostgreSQL schema: infrastructure_metrics, application_metrics, incidents,
  deployments, scaling_events, decisions, audit_log, users
- Prometheus + Grafana + cAdvisor monitoring
- Metrics-ingestion worker (Prometheus → Postgres)
- Locust-driven continuous real traffic
- XGBoost workload forecaster (time-aware split, baseline comparison)
- Isolation Forest anomaly detector (validated on controlled scenarios)
- Decision engine (recommendation mode first)
- Docker Compose–based scaling execution (manual-approve → auto)
- Basic cost calculation (replica-hours × published AWS rate)
- Self-healing restart action with audit log
- JWT auth
- Dashboard: Infra / AI Forecast / Incidents views
- Full Docker + docker-compose stack, deployed on EC2
- pytest suite covering models, auth, decision engine
- One full static-vs-predictive experiment run

## Tech Stack

FastAPI · React + Vite · PostgreSQL · Docker + Docker Compose ·
Prometheus + Grafana · Locust · XGBoost · Isolation Forest · AWS EC2/S3/IAM

## Out of Scope for P0

Six separate dashboards, full RBAC, real EC2 Auto Scaling Groups, CloudWatch,
RDS, deep-learning forecasting, automatic-mode scaling by default.
(See P1/P2 in the 80-day roadmap for when these get added.)

## Success Criteria (project-level definition of done)

- P0 pipeline runs end-to-end against real traffic — no synthetic CSV substituted anywhere
- Forecaster beats the naive-persistence baseline on MAE, using a time-aware
  (chronological) split with no leakage
- Anomaly detector correctly flags all 4 controlled scenarios (CPU spike,
  memory leak, latency spike, error-rate spike) with an acceptable
  false-positive rate during normal operation
- Decision engine executes at least one real scale-up and one real
  scale-down action, both logged in `scaling_events`
- Self-healing recovers from a controlled container-kill, with MTTR measured
  and logged
- 3-way experiment (static vs. reactive vs. predictive) completed with real
  logged cost/latency/SLA numbers — no invented results
- Full stack deployed and reachable on AWS EC2
- Every automated action is traceable in `audit_log`
