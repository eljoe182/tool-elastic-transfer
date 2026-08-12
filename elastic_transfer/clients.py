"""Elasticsearch client factories."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from elastic_transfer.config import ClusterConfig


def create_client(config: ClusterConfig) -> Elasticsearch:
    """Create an Elasticsearch client for the given cluster config."""
    return Elasticsearch(
        config.url,
        basic_auth=(config.username, config.password),
        verify_certs=True,
        request_timeout=120,
    )
