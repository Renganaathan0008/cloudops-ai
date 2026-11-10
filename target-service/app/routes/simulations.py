"""Opt-in latency, CPU, memory, and error-rate test endpoints."""

import asyncio
import math
import random
import threading
import time
from typing import Annotated

from app.schemas import MemoryLeakRequest, MemoryLeakStatus
from app.simulate.memory import memory_growth_simulator
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/simulate", tags=["simulation"])

MAX_CPU_DURATION_SECONDS = 2.0
_cpu_guard = threading.Lock()


@router.get("/latency")
async def simulate_latency(
    delay_seconds: Annotated[float, Query(ge=0, le=5)] = 0.1,
) -> dict[str, float | str]:
    """Wait asynchronously to create a bounded response-time workload."""

    started_at = time.perf_counter()
    await asyncio.sleep(delay_seconds)
    elapsed_seconds = time.perf_counter() - started_at
    return {
        "simulation": "latency",
        "configured_delay_seconds": delay_seconds,
        "actual_elapsed_seconds": elapsed_seconds,
    }


def _consume_cpu(duration_seconds: float) -> int:
    """Use one worker thread for a bounded CPU workload."""

    deadline = time.perf_counter() + duration_seconds
    iterations = 0
    value = 0.123456789
    while time.perf_counter() < deadline:
        value = math.sin(value + 0.001) * math.cos(value + 0.002)
        iterations += 1
    return iterations + int(value == -1.0)


@router.get("/cpu-load")
async def simulate_cpu_load(
    duration_seconds: Annotated[
        float,
        Query(ge=0.01, le=MAX_CPU_DURATION_SECONDS),
    ] = 0.1,
) -> dict[str, float | int | str]:
    """Run a short CPU workload in one worker thread.

    The maximum duration is 2 s.
    """

    if not _cpu_guard.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A CPU simulation is already running.",
        )

    started_at = time.perf_counter()
    try:
        iterations = await asyncio.to_thread(_consume_cpu, duration_seconds)
    finally:
        _cpu_guard.release()

    return {
        "simulation": "cpu-load",
        "requested_duration_seconds": duration_seconds,
        "actual_execution_seconds": time.perf_counter() - started_at,
        "iterations": iterations,
    }


@router.post("/memory-leak", response_model=MemoryLeakStatus)
async def configure_memory_growth(
    config: MemoryLeakRequest,
) -> MemoryLeakStatus:
    """Enable or disable the bounded memory growth simulation."""

    try:
        return await memory_growth_simulator.configure(config)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get("/memory-leak/status", response_model=MemoryLeakStatus)
def memory_growth_status() -> MemoryLeakStatus:
    """Inspect current simulated allocation and its hard cap."""

    return memory_growth_simulator.status()


@router.get("/error-rate")
def simulate_error_rate(
    probability: Annotated[float, Query(ge=0, le=1)] = 0.0,
) -> dict[str, float | str]:
    """Return success or a controlled 503 according to the requested
    probability.
    """

    outcome = "failure" if random.random() < probability else "success"
    if outcome == "failure":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"probability": probability, "outcome": outcome},
        )
    return {"probability": probability, "outcome": outcome}
