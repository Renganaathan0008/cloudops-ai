"""Prometheus metrics backed by real requests and psutil measurements."""

import os

import psutil
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "cloudops_target_http_requests_total",
    "HTTP requests handled by the target service.",
    ("method", "endpoint", "status_code"),
)
HTTP_REQUEST_DURATION = Histogram(
    "cloudops_target_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "endpoint", "status_code"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

SYSTEM_CPU_PERCENT = Gauge(
    "cloudops_target_system_cpu_percent",
    "System CPU utilization reported by psutil, in percent.",
)
PROCESS_CPU_PERCENT = Gauge(
    "cloudops_target_process_cpu_percent",
    "Target service process CPU utilization reported by psutil, in percent.",
)
SYSTEM_MEMORY_PERCENT = Gauge(
    "cloudops_target_system_memory_percent",
    "System memory utilization reported by psutil, in percent.",
)
SYSTEM_MEMORY_TOTAL_BYTES = Gauge(
    "cloudops_target_system_memory_total_bytes",
    "Total system memory reported by psutil, in bytes.",
)
SYSTEM_MEMORY_AVAILABLE_BYTES = Gauge(
    "cloudops_target_system_memory_available_bytes",
    "Available system memory reported by psutil, in bytes.",
)
PROCESS_MEMORY_RSS_BYTES = Gauge(
    "cloudops_target_process_memory_rss_bytes",
    "Resident memory of the target service process, in bytes.",
)
PROCESS_MEMORY_VMS_BYTES = Gauge(
    "cloudops_target_process_memory_vms_bytes",
    "Virtual memory of the target service process, in bytes.",
)
ACTIVE_ITEMS = Gauge(
    "cloudops_target_active_items",
    "Number of items currently held in the in-memory store.",
)
MEMORY_SIMULATION_ENABLED = Gauge(
    "cloudops_target_memory_simulation_enabled",
    "Whether bounded memory growth simulation is enabled (1 or 0).",
)
MEMORY_SIMULATION_ALLOCATED_BYTES = Gauge(
    "cloudops_target_memory_simulation_allocated_bytes",
    "Bytes retained by the bounded memory growth simulation.",
)


def update_runtime_metrics(active_item_count: int) -> None:
    """Refresh gauges from the current process, host, and in-memory store."""

    process = psutil.Process(os.getpid())
    virtual_memory = psutil.virtual_memory()

    SYSTEM_CPU_PERCENT.set(psutil.cpu_percent(interval=None))
    PROCESS_CPU_PERCENT.set(process.cpu_percent(interval=None))
    SYSTEM_MEMORY_PERCENT.set(virtual_memory.percent)
    SYSTEM_MEMORY_TOTAL_BYTES.set(virtual_memory.total)
    SYSTEM_MEMORY_AVAILABLE_BYTES.set(virtual_memory.available)

    process_memory = process.memory_info()
    PROCESS_MEMORY_RSS_BYTES.set(process_memory.rss)
    PROCESS_MEMORY_VMS_BYTES.set(process_memory.vms)
    ACTIVE_ITEMS.set(active_item_count)
