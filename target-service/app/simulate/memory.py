"""Bounded, opt-in memory growth for monitoring experiments."""

import asyncio
from asyncio import Task

import app.metrics as metrics_module
from app.schemas import MemoryLeakRequest, MemoryLeakStatus

MAX_MEMORY_BYTES = 8 * 1024 * 1024
_PAGE_SIZE = 4_096


class MemoryGrowthSimulator:
    """Allocate touched bytearrays at a controlled rate up to a hard cap."""

    def __init__(self) -> None:
        self.enabled = False
        self.allocated_bytes = 0
        self.allocation_interval_seconds = 0.5
        self.allocation_bytes_per_interval = 262_144
        self._chunks: list[bytearray] = []
        self._task: Task[None] | None = None

    def status(self) -> MemoryLeakStatus:
        return MemoryLeakStatus(
            enabled=self.enabled,
            allocated_bytes=self.allocated_bytes,
            max_memory_bytes=MAX_MEMORY_BYTES,
            allocation_interval_seconds=self.allocation_interval_seconds,
            allocation_bytes_per_interval=self.allocation_bytes_per_interval,
        )

    async def configure(self, config: MemoryLeakRequest) -> MemoryLeakStatus:
        if not config.enabled:
            await self.disable()
            return self.status()

        if self.allocated_bytes >= MAX_MEMORY_BYTES:
            raise ValueError(
                "Memory cap reached; disable the simulation to release it."
            )

        self.allocation_interval_seconds = config.allocation_interval_seconds
        allocation_bytes = config.allocation_bytes_per_interval
        self.allocation_bytes_per_interval = allocation_bytes
        if self._task is None or self._task.done():
            self.enabled = True
            metrics_module.MEMORY_SIMULATION_ENABLED.set(1)
            self._task = asyncio.create_task(self._grow())
        else:
            self.enabled = True
            metrics_module.MEMORY_SIMULATION_ENABLED.set(1)
        return self.status()

    async def disable(self) -> None:
        """Stop future allocations and release all simulated memory."""

        self.enabled = False
        metrics_module.MEMORY_SIMULATION_ENABLED.set(0)
        task = self._task
        self._task = None
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._chunks.clear()
        self.allocated_bytes = 0
        metrics_module.MEMORY_SIMULATION_ALLOCATED_BYTES.set(0)

    async def _grow(self) -> None:
        current_task = asyncio.current_task()
        try:
            while self.enabled:
                await asyncio.sleep(self.allocation_interval_seconds)
                if not self.enabled:
                    break

                remaining_bytes = MAX_MEMORY_BYTES - self.allocated_bytes
                if remaining_bytes <= 0:
                    self.enabled = False
                    metrics_module.MEMORY_SIMULATION_ENABLED.set(0)
                    break

                allocation_size = min(
                    self.allocation_bytes_per_interval,
                    remaining_bytes,
                )
                chunk = bytearray(allocation_size)
                for offset in range(0, allocation_size, _PAGE_SIZE):
                    chunk[offset] = 1
                self._chunks.append(chunk)
                self.allocated_bytes += allocation_size
                metrics_module.MEMORY_SIMULATION_ALLOCATED_BYTES.set(
                    self.allocated_bytes,
                )

                if self.allocated_bytes >= MAX_MEMORY_BYTES:
                    self.enabled = False
                    metrics_module.MEMORY_SIMULATION_ENABLED.set(0)
        finally:
            if self._task is current_task:
                self._task = None


memory_growth_simulator = MemoryGrowthSimulator()
