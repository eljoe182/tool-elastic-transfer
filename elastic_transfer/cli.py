"""CLI entry point for elastic-transfer."""

from __future__ import annotations

import argparse
import sys

from elastic_transfer.clients import create_client
from elastic_transfer.config import load_config
from elastic_transfer.index_ops import (
    create_index_from_origin,
    delete_index,
    empty_index,
    index_exists,
    list_indices,
)
from elastic_transfer.transfer import transfer_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="elastic-transfer",
        description=(
            "Migrate an Elasticsearch index from an origin cluster "
            "to a destination cluster."
        ),
    )
    parser.add_argument(
        "--index",
        help="Index name to read from origin and write to destination",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--update",
        action="store_true",
        help=(
            "If the destination index exists, empty it then insert origin "
            "documents (default)"
        ),
    )
    mode.add_argument(
        "--recreate",
        action="store_true",
        help=(
            "If the destination index exists, delete it, recreate it from "
            "origin settings/mappings, then transfer"
        ),
    )
    mode.add_argument(
        "--delete",
        action="store_true",
        help="Delete the index on the cluster specified by --cluster",
    )
    mode.add_argument(
        "--list",
        action="store_true",
        help="List all indices on the cluster specified by --cluster",
    )
    parser.add_argument(
        "--cluster",
        choices=["origin", "destination"],
        help="Cluster to target (required with --delete or --list)",
    )
    return parser


def prepare_destination(
    origin,
    destination,
    index: str,
    *,
    recreate: bool,
) -> None:
    exists = index_exists(destination, index)

    if not exists:
        print(f"Destination index '{index}' does not exist; creating from origin...")
        create_index_from_origin(origin, destination, index)
        print(f"Created destination index '{index}'.")
        return

    if recreate:
        print(f"Recreating destination index '{index}' from origin...")
        delete_index(destination, index)
        create_index_from_origin(origin, destination, index)
        print(f"Recreated destination index '{index}'.")
        return

    print(f"Emptying destination index '{index}' (--update)...")
    empty_index(destination, index)
    print(f"Destination index '{index}' emptied.")


def run_delete(index: str, cluster: str) -> int:
    config = load_config()
    cluster_config = config.origin if cluster == "origin" else config.destination
    client = create_client(cluster_config)

    try:
        try:
            if not index_exists(client, index):
                print(
                    f"Error: index '{index}' does not exist on {cluster} cluster.",
                    file=sys.stderr,
                )
                return 1
        except Exception as exc:
            raise RuntimeError(f"Failed talking to {cluster} cluster: {exc}") from exc

        delete_index(client, index)
        print(f"Deleted index '{index}' from {cluster} cluster.")
        return 0
    finally:
        client.close()


def _print_indices_table(indices: list[dict[str, str]]) -> None:
    headers = ("INDEX", "HEALTH", "STATUS", "DOCS", "SIZE")
    rows = [
        (
            entry.get("index", ""),
            entry.get("health", ""),
            entry.get("status", ""),
            entry.get("docs.count", ""),
            entry.get("store.size", ""),
        )
        for entry in indices
    ]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows))
        for i in range(len(headers))
    ]
    header_line = "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))
    print(header_line)
    for row in rows:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(row))))


def run_list(cluster: str) -> int:
    config = load_config()
    cluster_config = config.origin if cluster == "origin" else config.destination
    client = create_client(cluster_config)

    try:
        try:
            indices = list_indices(client)
        except Exception as exc:
            raise RuntimeError(f"Failed talking to {cluster} cluster: {exc}") from exc

        if not indices:
            print(f"No indices found on {cluster} cluster.")
            return 0

        _print_indices_table(indices)
        return 0
    finally:
        client.close()


def run(index: str, recreate: bool) -> int:
    config = load_config()
    origin = create_client(config.origin)
    destination = create_client(config.destination)

    try:
        try:
            if not index_exists(origin, index):
                print(f"Error: origin index '{index}' does not exist.", file=sys.stderr)
                return 1
        except Exception as exc:
            raise RuntimeError(f"Failed talking to origin cluster: {exc}") from exc

        print(f"Origin index '{index}' found.")

        try:
            prepare_destination(origin, destination, index, recreate=recreate)
        except Exception as exc:
            raise RuntimeError(f"Failed preparing destination cluster: {exc}") from exc

        print(f"Starting transfer for '{index}'...")
        try:
            transferred = transfer_documents(origin, destination, index)
        except Exception as exc:
            raise RuntimeError(f"Failed during document transfer: {exc}") from exc

        print(f"Done. Transferred {transferred} document(s) to '{index}'.")
        return 0
    finally:
        origin.close()
        destination.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        if not args.cluster:
            parser.error("--cluster is required when using --list")
        if args.index:
            parser.error("--index cannot be used with --list")
    elif args.delete:
        if not args.cluster:
            parser.error("--cluster is required when using --delete")
        if not args.index:
            parser.error("--index is required when using --delete")
    elif args.cluster:
        parser.error("--cluster can only be used with --delete or --list")
    elif not args.index:
        parser.error("--index is required")

    try:
        if args.list:
            return run_list(args.cluster)
        if args.delete:
            return run_delete(args.index, args.cluster)
        # Default mode is update when neither flag is set.
        return run(args.index, recreate=bool(args.recreate))
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
