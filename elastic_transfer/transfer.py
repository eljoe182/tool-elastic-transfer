"""Scroll origin documents and bulk-index them into the destination."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

DEFAULT_BATCH_SIZE = 500


def _actions(
    origin: Elasticsearch,
    index: str,
    batch_size: int,
) -> Iterator[dict[str, Any]]:
    for doc in helpers.scan(
        origin,
        index=index,
        query={"query": {"match_all": {}}},
        size=batch_size,
        preserve_order=False,
        clear_scroll=True,
    ):
        action: dict[str, Any] = {
            "_op_type": "index",
            "_index": index,
            "_source": doc.get("_source", {}),
        }
        doc_id = doc.get("_id")
        if doc_id is not None:
            action["_id"] = doc_id
        routing = doc.get("_routing")
        if routing is not None:
            action["_routing"] = routing
        yield action


def transfer_documents(
    origin: Elasticsearch,
    destination: Elasticsearch,
    index: str,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """
    Copy all documents from origin to destination for ``index``.

    Returns the number of successfully indexed documents.
    Raises on bulk item errors (hard stop).
    """
    total = origin.count(index=index).get("count", 0)
    if total == 0:
        print(f"Origin index '{index}' has 0 documents; nothing to transfer.")
        return 0

    success = 0
    errors: list[Any] = []

    with tqdm(total=total, unit="docs", desc=f"Transferring {index}") as bar:
        for ok, item in helpers.streaming_bulk(
            destination,
            _actions(origin, index, batch_size),
            chunk_size=batch_size,
            raise_on_error=False,
            raise_on_exception=True,
        ):
            if ok:
                success += 1
            else:
                errors.append(item)
            bar.update(1)

    if errors:
        sample = errors[:5]
        raise RuntimeError(
            f"Bulk indexing failed for {len(errors)} document(s). "
            f"Sample errors: {sample}"
        )

    return success
