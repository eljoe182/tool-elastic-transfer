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

# Delete index on destination cluster
poetry run elastic-transfer --delete --index my-index --cluster destination

# Delete index on origin cluster
poetry run elastic-transfer --delete --index my-index --cluster origin

# List all indices on origin cluster
poetry run elastic-transfer --list --cluster origin

# List all indices on destination cluster
poetry run elastic-transfer --list --cluster destination
```

### Modes

| Mode | Destination missing | Destination exists |
|---|---|---|
| `--update` (default) | Create from origin, then transfer | Empty documents (`delete_by_query`), then transfer |
| `--recreate` | Create from origin, then transfer | Delete index, create from origin, then transfer |

### Delete mode

Use `--delete` with `--cluster origin` or `--cluster destination` to remove an index from a single cluster. The tool connects only to the chosen cluster and deletes the index entirely (settings, mappings, and documents). The index must exist on that cluster or the command exits with an error.

### List mode

Use `--list` with `--cluster origin` or `--cluster destination` to show all indices on the chosen cluster. Output includes index name, health, status, document count, and store size. System/hidden indices are included.

The same index name is used on origin and destination. Document `_id` values are preserved. Progress is shown with a progress bar during transfer.

## Run as a module

```bash
poetry run python -m elastic_transfer --index my-index
```
