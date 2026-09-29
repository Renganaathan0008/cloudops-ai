# Module Boundaries

## cloudops-backend/ (FastAPI control plane)
cloudops-backend/
|-- app/
| |-- main.py # FastAPI app entrypoint
| |-- core/ # config, settings, security/JWT utils
| |-- models/ # SQLAlchemy models (1 file per table)
| |-- schemas/ # Pydantic request/response schemas
| |-- api/ # route modules (metrics, incidents,
| | # deployments, decisions, auth, cost)
| |-- ingestion/ # Prometheus-poll -> Postgres worker
| |-- ml/ # loads serialized model, /predict logic
| |-- anomaly/ # loads Isolation Forest, scoring logic
| |-- decision_engine/ # forecast+anomaly+state -> recommendation
| |-- cost/ # cost calculation + rightsizing logic
| |-- actions/ # allowlisted executor (compose/ECS/heal)
| -- db.py # SQLAlchemy session/engine setup |-- alembic/ # migrations |-- tests/ # pytest, mirrors app/ structure |-- Dockerfile -- requirements.txt

## target-service/ (monitored demo app)
target-service/
|-- app/
| |-- main.py # FastAPI app + /metrics via prometheus_client
| |-- routes/ # /items CRUD, variable-latency endpoints
| -- simulate/ # cpu-load, memory-leak, error-rate toggles |-- Dockerfile -- requirements.txt

## dashboard/ (React + Vite)
dashboard/
|-- src/
| |-- views/ # Infra, Forecast, Cost, Incidents, Deploy
| |-- api/ # fetch wrappers to cloudops-backend
| |-- components/
| -- App.tsx |-- Dockerfile -- package.json

## ml/ (offline training pipeline - not a live service)
ml/
|-- notebooks/ # EDA
|-- features.py # lag/rolling feature engineering
|-- train_forecaster.py # baseline -> RF -> XGBoost, time-aware split
|-- train_anomaly.py # Isolation Forest training
|-- evaluate.py # MAE/RMSE/MAPE/R2 comparison
`-- models/ # serialized .joblib output (gitignored)

## infra/
infra/
|-- docker-compose.yml
|-- prometheus/prometheus.yml
|-- grafana/provisioning/
`-- deploy/ # EC2 setup + deploy scripts
