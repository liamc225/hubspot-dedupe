from __future__ import annotations

from dataclasses import asdict
from importlib.resources import files
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from hubspot_dedupe.engine import find_duplicate_clusters
from hubspot_dedupe.io import load_records_from_bytes, load_records_from_text
from hubspot_dedupe.models import DuplicateCluster, ObjectType, PairMatch, Record


OBJECT_TYPES: tuple[ObjectType, ...] = ("contacts", "companies")
STATIC_ROOT = files("hubspot_dedupe.web").joinpath("static")
SAMPLE_ROOT = files("hubspot_dedupe.web").joinpath("samples")


def _read_asset(name: str) -> str:
    return STATIC_ROOT.joinpath(name).read_text(encoding="utf-8")


INDEX_HTML = _read_asset("index.html")
APP_CSS = _read_asset("app.css")
APP_JS = _read_asset("app.js")


def create_app() -> FastAPI:
    app = FastAPI(
        title="HubSpot Dedupe UI",
        summary="Self-hosted UI for deduplicating HubSpot exports.",
        version="0.1.0",
    )

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(INDEX_HTML)

    @app.get("/assets/app.css")
    def stylesheet() -> Response:
        return Response(APP_CSS, media_type="text/css")

    @app.get("/assets/app.js")
    def script() -> Response:
        return Response(APP_JS, media_type="text/javascript")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/samples/{object_type}")
    def analyze_sample(object_type: ObjectType, min_score: int = 70) -> JSONResponse:
        _validate_object_type(object_type)
        csv_text = SAMPLE_ROOT.joinpath(f"sample_{object_type}.csv").read_text(encoding="utf-8")
        records = load_records_from_text(csv_text, object_type)
        return JSONResponse(_analysis_payload(object_type, records, min_score, f"sample_{object_type}.csv"))

    @app.post("/api/analyze")
    async def analyze_upload(
        object_type: Annotated[ObjectType, Form()],
        min_score: Annotated[int, Form(ge=0, le=100)] = 70,
        csv_file: UploadFile = File(...),
    ) -> JSONResponse:
        _validate_object_type(object_type)
        file_bytes = await csv_file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Upload a non-empty CSV file.")

        try:
            records = load_records_from_bytes(file_bytes, object_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        source_name = csv_file.filename or "uploaded.csv"
        return JSONResponse(_analysis_payload(object_type, records, min_score, source_name))

    return app


def _analysis_payload(
    object_type: ObjectType,
    records: list[Record],
    min_score: int,
    source_name: str,
) -> dict[str, object]:
    clusters = find_duplicate_clusters(object_type, records, min_score=min_score)
    merge_count = sum(max(len(cluster.records) - 1, 0) for cluster in clusters)

    return {
        "object_type": object_type,
        "source_name": source_name,
        "min_score": min_score,
        "record_count": len(records),
        "cluster_count": len(clusters),
        "merge_count": merge_count,
        "clusters": [_serialize_cluster(cluster) for cluster in clusters],
    }


def _serialize_cluster(cluster: DuplicateCluster) -> dict[str, object]:
    actions = []
    for record in cluster.records:
        if record.record_id == cluster.master_record.record_id:
            continue
        pair_match = _best_pair_for_record(cluster, record.record_id)
        actions.append(
            {
                "duplicate_id": record.record_id,
                "duplicate_label": _record_label(record),
                "score": pair_match.score,
                "reasons": pair_match.reasons,
            }
        )

    return {
        "cluster_id": cluster.cluster_id,
        "confidence": cluster.confidence,
        "score": cluster.score,
        "master_record": asdict(cluster.master_record),
        "master_label": _record_label(cluster.master_record),
        "records": [asdict(record) for record in cluster.records],
        "actions": actions,
    }


def _record_label(record: Record) -> str:
    if getattr(record, "email", None):
        return f"{record.record_id} · {getattr(record, 'email')}"
    if getattr(record, "name", None):
        return f"{record.record_id} · {getattr(record, 'name')}"

    first_name = getattr(record, "first_name", None)
    last_name = getattr(record, "last_name", None)
    if first_name or last_name:
        name = " ".join(part for part in [first_name, last_name] if part)
        return f"{record.record_id} · {name}"

    return str(record.record_id)


def _best_pair_for_record(cluster: DuplicateCluster, record_id: str) -> PairMatch:
    relevant_matches = [
        pair_match
        for pair_match in cluster.pair_matches
        if pair_match.left_id == record_id or pair_match.right_id == record_id
    ]
    return max(relevant_matches, key=lambda pair_match: pair_match.score)


def _validate_object_type(object_type: ObjectType) -> None:
    if object_type not in OBJECT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported object type.")


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    uvicorn.run(
        "hubspot_dedupe.web.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
