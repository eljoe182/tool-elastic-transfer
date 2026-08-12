# Elastic Transfer

CLI tool to migrate an Elasticsearch index from an origin cluster to a destination cluster using scroll + bulk.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
cp .env.example .env
# Fill in origin and destination credentials in .env

poetry install
```

## Environment variables

| Variable | Description |
|---|---|
| `ELASTICSEARCH_URL_ORIGIN` | Origin cluster URL (`http://` or `https://`) |
| `ELASTICSEARCH_USERNAME_ORIGIN` | Origin username |
| `ELASTICSEARCH_PASSWORD_ORIGIN` | Origin password |
| `ELASTICSEARCH_VERIFY_CERTS_ORIGIN` | Verify TLS certs for origin (`true`/`false`, default `true`) |
| `ELASTICSEARCH_URL_DESTINATION` | Destination cluster URL (`http://` or `https://`) |
| `ELASTICSEARCH_USERNAME_DESTINATION` | Destination username |
| `ELASTICSEARCH_PASSWORD_DESTINATION` | Destination password |
| `ELASTICSEARCH_VERIFY_CERTS_DESTINATION` | Verify TLS certs for destination (`true`/`false`, default `true`) |

For local clusters behind `kubectl port-forward` with HTTPS and a self-signed certificate, use `https://` in the URL and set `ELASTICSEARCH_VERIFY_CERTS_DESTINATION=false`.

## Usage

```bash
# Default mode (--update): if destination index exists, empty it then transfer
poetry run elastic-transfer --index my-index

# Explicit update mode
poetry run elastic-transfer --index my-index --update

# Recreate destination from origin settings/mappings, then transfer
poetry run elastic-transfer --index my-index --recreate
```

### Modes

| Mode | Destination missing | Destination exists |
|---|---|---|
| `--update` (default) | Create from origin, then transfer | Empty documents (`delete_by_query`), then transfer |
| `--recreate` | Create from origin, then transfer | Delete index, create from origin, then transfer |

The same index name is used on origin and destination. Document `_id` values are preserved. Progress is shown with a progress bar during transfer.

## Run as a module

```bash
poetry run python -m elastic_transfer --index my-index
```
