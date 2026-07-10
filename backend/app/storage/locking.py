from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock
from uuid import UUID

_locks_guard = Lock()
_document_locks: dict[UUID, Lock] = {}


@contextmanager
def document_lock(document_id: UUID) -> Iterator[None]:
    with _locks_guard:
        lock = _document_locks.setdefault(document_id, Lock())
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
