# ADR-0001: Modular Monolith over Microservices

## Status

Accepted — 2026 (Day 2 of build)

## Context

CloudOps AI has four logical modules: target-service, cloudops-backend,
ml pipeline, and dashboard. A microservices split (e.g., separate services
for forecasting, anomaly detection, decision engine, cost engine) was
considered since the architecture diagram already shows these as distinct
boxes.

## Decision

Each box in the architecture diagram is implemented as a **Python module
within cloudops-backend** (ml inference, decision engine, cost engine,
action executor all live in-process), not as separate deployable services.
Only target-service and dashboard are separate containers, because they
have genuinely different runtimes (a monitored app under test; a browser
frontend). The ML _training_ pipeline (`ml/`) runs offline/on-demand, not
as a live service — it produces artifacts that cloudops-backend loads.

## Rationale

- A single developer building this in 80 days cannot absorb the
  operational cost of inter-service auth, service discovery, and
  distributed tracing that real microservices require.
- The modules communicate via simple function calls and one shared
  Postgres database — there is no scaling or fault-isolation reason
  (yet) that any module needs independent deployment.
- The mega-prompt's own design principle explicitly says: "avoid
  unnecessary microservices; if a modular monolith is more appropriate
  initially, recommend it."

## Consequences

- **Positive:** faster iteration, one Dockerfile to maintain for the
  backend, no network-call failure modes between decision engine and
  ML inference.
- **Negative:** cloudops-backend will grow large; internal module
  boundaries (`app/ml/`, `app/decision_engine/`, `app/cost/`,
  `app/actions/`) must stay disciplined so a future split is possible
  if ever needed.
- **Revisit trigger:** if any single module needs independent scaling
  or a different language/runtime, reconsider extraction — not before.
