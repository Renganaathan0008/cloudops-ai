"""Pydantic schemas used by the target service API."""

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Fields accepted when creating an item."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: float = Field(ge=0, le=1_000_000)


class ItemUpdate(ItemCreate):
    """Fields required when replacing an existing item."""


class ItemRead(BaseModel):
    """Item representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: float


class MemoryLeakRequest(BaseModel):
    """Controls bounded memory growth for local monitoring tests."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    allocation_interval_seconds: float = Field(default=0.5, ge=0.05, le=60)
    allocation_bytes_per_interval: int = Field(
        default=262_144,
        ge=1_024,
        le=1_048_576,
    )


class MemoryLeakStatus(BaseModel):
    """Current state of the memory growth simulation."""

    enabled: bool
    allocated_bytes: int
    max_memory_bytes: int
    allocation_interval_seconds: float
    allocation_bytes_per_interval: int
