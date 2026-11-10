"""FastAPI entry point for the CloudOps AI target service."""

from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncIterator

import app.metrics as metrics_module
from app.routes.items import item_store
from app.routes.items import router as items_router
from app.routes.simulations import router as simulations_router
from app.simulate.memory import memory_growth_simulator
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release simulated allocations when the service shuts down."""

    yield
    await memory_growth_simulator.disable()


app = FastAPI(
    title="CloudOps AI Target Service",
    description=(
        "A small workload source for CloudOps AI monitoring experiments. "
        "Items are held in memory and reset when the service restarts."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(items_router)
app.include_router(simulations_router)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next) -> Response:
    """Count requests by stable route template and observe their duration."""

    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        endpoint = getattr(route, "path", "unmatched")
        labels = (request.method, endpoint, str(status_code))
        metrics_module.HTTP_REQUESTS.labels(*labels).inc()
        request_duration = perf_counter() - started_at
        duration_metric = metrics_module.HTTP_REQUEST_DURATION
        duration_metric.labels(*labels).observe(request_duration)
        metrics_module.update_runtime_metrics(item_store.count())


@app.get("/", tags=["service"])
def root() -> dict[str, str]:
    """Describe the target service and its in-memory data lifecycle."""

    storage = "Items are stored in memory and reset when the app restarts."
    return {
        "service": "CloudOps AI Target Service",
        "message": "Workload and item API for monitoring experiments.",
        "data_storage": storage,
    }


@app.get("/health", tags=["service"])
def health() -> dict[str, str]:
    """Return a simple health response."""

    return {"status": "ok", "service": "target-service"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Expose Prometheus request and real psutil system/process metrics."""

    metrics_module.update_runtime_metrics(item_store.count())
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
