# CloudOps AI

Intelligent cloud-native platform for predictive auto-scaling, cost optimization, anomaly detection, and self-healing.

## Status

In active development — Day 1 of an 80-day build.

## Structure

- `target-service/` — instrumented demo service CloudOps AI monitors and manages
- `cloudops-backend/` — FastAPI control plane (metrics, ML inference, decision engine, API)
- `dashboard/` — React + Vite frontend
- `ml/` — forecasting + anomaly detection training pipeline
- `infra/` — Docker Compose, Prometheus/Grafana configs, deployment scripts
- `docs/` — architecture, API, and project documentation
