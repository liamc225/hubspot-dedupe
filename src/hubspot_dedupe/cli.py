from __future__ import annotations

import argparse
import json
import sys

from hubspot_dedupe.engine import cluster_to_dict, find_duplicate_clusters
from hubspot_dedupe.io import load_records
from hubspot_dedupe.models import DuplicateCluster, ObjectType
from hubspot_dedupe.web import run_server


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    if args and args[0] == "serve":
        _serve(args[1:])
        return

    _run_legacy(args)


def _run_legacy(args: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Detect duplicate HubSpot records from a CSV export.")
    parser.add_argument("object_type", choices=["contacts", "companies"])
    parser.add_argument("path", help="Path to a HubSpot CSV export.")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum score to treat a pair as a duplicate.")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    parsed_args = parser.parse_args(args)

    object_type = parsed_args.object_type
    records = load_records(parsed_args.path, object_type)
    clusters = find_duplicate_clusters(object_type, records, min_score=parsed_args.min_score)

    if parsed_args.format == "json":
        print(json.dumps([cluster_to_dict(cluster) for cluster in clusters], indent=2))
        return

    print(render_markdown(object_type, clusters))


def _serve(args: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Run the self-hosted HubSpot Dedupe web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for local development.")
    parsed_args = parser.parse_args(args)
    run_server(host=parsed_args.host, port=parsed_args.port, reload=parsed_args.reload)


def render_markdown(object_type: ObjectType, clusters: list[DuplicateCluster]) -> str:
    if not clusters:
        return f"No duplicate {object_type} found."

    lines: list[str] = []
    for cluster in clusters:
        master_display = _record_summary(cluster.master_record)
        lines.append(
            f"Cluster {cluster.cluster_id} | confidence: {cluster.confidence} | score: {cluster.score}"
        )
        lines.append(f"Master: {master_display}")

        for duplicate_id in _duplicate_ids(cluster):
            pair_match = _best_pair_for_record(cluster, duplicate_id)
            reason_text = ", ".join(pair_match.reasons) if pair_match.reasons else "manual review"
            lines.append(
                f"- Merge {duplicate_id} into {cluster.master_record.record_id} | score: {pair_match.score} | reasons: {reason_text}"
            )
        lines.append("")

    return "\n".join(lines).strip()


def _record_summary(record: object) -> str:
    record_id = getattr(record, "record_id")
    if hasattr(record, "email") and getattr(record, "email"):
        return f"{record_id} ({getattr(record, 'email')})"
    if hasattr(record, "name"):
        return f"{record_id} ({getattr(record, 'name')})"
    return str(record_id)


def _duplicate_ids(cluster: DuplicateCluster) -> list[str]:
    return [
        record.record_id
        for record in cluster.records
        if record.record_id != cluster.master_record.record_id
    ]


def _best_pair_for_record(cluster: DuplicateCluster, record_id: str):
    relevant_matches = [
        pair_match
        for pair_match in cluster.pair_matches
        if pair_match.left_id == record_id or pair_match.right_id == record_id
    ]
    return max(relevant_matches, key=lambda pair_match: pair_match.score)


if __name__ == "__main__":
    main()
