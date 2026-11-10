"""In-memory CRUD endpoints for target-service items."""

from threading import Lock
from typing import Annotated

from app.schemas import ItemCreate, ItemRead, ItemUpdate
from fastapi import APIRouter, HTTPException, Path, Response, status

router = APIRouter(prefix="/items", tags=["items"])


class ItemStore:
    """Small thread-safe in-memory item store; contents reset on restart."""

    def __init__(self) -> None:
        self._items: dict[int, ItemRead] = {}
        self._next_id = 1
        self._lock = Lock()

    def create(self, item: ItemCreate) -> ItemRead:
        with self._lock:
            item_id = self._next_id
            self._next_id += 1
            saved_item = ItemRead(id=item_id, **item.model_dump())
            self._items[item_id] = saved_item
            return saved_item

    def list(self) -> list[ItemRead]:
        with self._lock:
            return list(self._items.values())

    def get(self, item_id: int) -> ItemRead | None:
        with self._lock:
            return self._items.get(item_id)

    def update(self, item_id: int, item: ItemUpdate) -> ItemRead | None:
        with self._lock:
            if item_id not in self._items:
                return None
            updated_item = ItemRead(id=item_id, **item.model_dump())
            self._items[item_id] = updated_item
            return updated_item

    def delete(self, item_id: int) -> bool:
        with self._lock:
            return self._items.pop(item_id, None) is not None

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        """Clear items, primarily for test isolation."""

        with self._lock:
            self._items.clear()
            self._next_id = 1


item_store = ItemStore()


def get_existing_item(item_id: int) -> ItemRead:
    item = item_store.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} was not found.",
        )
    return item


@router.get("", response_model=list[ItemRead])
def list_items() -> list[ItemRead]:
    """Return every item currently in the in-memory store."""

    return item_store.list()


@router.get("/{item_id}", response_model=ItemRead)
def read_item(item_id: Annotated[int, Path(gt=0)]) -> ItemRead:
    """Return one item, or 404 when it does not exist."""

    return get_existing_item(item_id)


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate) -> ItemRead:
    """Create an item in memory; it will reset when the service restarts."""

    return item_store.create(item)


@router.put("/{item_id}", response_model=ItemRead)
def replace_item(
    item_id: Annotated[int, Path(gt=0)],
    item: ItemUpdate,
) -> ItemRead:
    """Replace an existing item, or return 404 when it does not exist."""

    updated_item = item_store.update(item_id, item)
    if updated_item is None:
        return get_existing_item(item_id)
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: Annotated[int, Path(gt=0)]) -> Response:
    """Delete an item and return an empty 204 response."""

    if not item_store.delete(item_id):
        get_existing_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
