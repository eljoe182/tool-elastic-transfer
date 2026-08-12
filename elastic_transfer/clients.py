"""Elasticsearch client factories."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from elastic_transfer.config import ClusterConfig


def create_client(config: ClusterConfig) -> Elasticsearch:
    """Create an Elasticsearch client for the given cluster config."""
    return Elasticsearch(
        config.url,
        basic_auth=(config.username, config.password),
        verify_certs=config.verify_certs,
        ssl_show_warn=config.verify_certs,
        request_timeout=120,
        max_retries=3,
        retry_on_timeout=True,
    )
