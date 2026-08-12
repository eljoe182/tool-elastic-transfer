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
        required=True,
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
    recreate = bool(args.recreate)
    # Default mode is update when neither flag is set.
    try:
        return run(args.index, recreate=recreate)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
