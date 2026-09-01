"""Index existence, creation, deletion, and emptying helpers."""

from __future__ import annotations

import copy
from typing import Any

from elasticsearch import Elasticsearch

# Settings keys that cannot (or should not) be sent on index create.
_INDEX_SETTINGS_BLOCKLIST = frozenset(
    {
        "uuid",
        "creation_date",
        "creation_date_string",
        "version",
        "provided_name",
        "routing_path",
        "resize",
        "routing_num_shards",
    }
)


def index_exists(client: Elasticsearch, index: str) -> bool:
    return bool(client.indices.exists(index=index))


def get_index_definition(client: Elasticsearch, index: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return sanitized settings and mappings suitable for creating the index elsewhere."""
    response = client.indices.get(index=index)
    # Response keys are index names; use the first (exact match for a concrete index).
    body = response[index] if index in response else next(iter(response.values()))
    settings = sanitize_settings(body.get("settings", {}))
    mappings = body.get("mappings", {}) or {}
    return settings, mappings


def sanitize_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Strip non-creatable / cluster-specific index settings."""
    cleaned = copy.deepcopy(settings)
    index_settings = cleaned.get("index")
    if isinstance(index_settings, dict):
        for key in list(index_settings.keys()):
            if key in _INDEX_SETTINGS_BLOCKLIST:
                del index_settings[key]
        # Nested version block if present as a dict
        if "version" in index_settings:
            del index_settings["version"]
    return cleaned


def create_index(
    client: Elasticsearch,
    index: str,
    settings: dict[str, Any],
    mappings: dict[str, Any],
) -> None:
    kwargs: dict[str, Any] = {"index": index}
    if settings:
        kwargs["settings"] = settings
    if mappings:
        kwargs["mappings"] = mappings
    client.indices.create(**kwargs)


def delete_index(client: Elasticsearch, index: str) -> None:
    client.indices.delete(index=index)


def empty_index(client: Elasticsearch, index: str) -> None:
    """Remove all documents from the index while keeping settings and mappings."""
    client.delete_by_query(
        index=index,
        query={"match_all": {}},
        refresh=True,
        conflicts="proceed",
        wait_for_completion=True,
    )


def create_index_from_origin(
    origin: Elasticsearch,
    destination: Elasticsearch,
    index: str,
) -> None:
    settings, mappings = get_index_definition(origin, index)
    create_index(destination, index, settings, mappings)


def list_indices(client: Elasticsearch) -> list[dict[str, str]]:
    """Return all indices with health, status, doc count, and store size."""
    return client.cat.indices(
        index="*",
        format="json",
        h="index,health,status,docs.count,store.size",
        s="index",
        expand_wildcards="all",
    )
