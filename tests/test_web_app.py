from fastapi.testclient import TestClient

from hubspot_dedupe.cli import main
from hubspot_dedupe.web import create_app


def test_web_ui_root_renders_html() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "HubSpot Dedupe UI" in response.text


def test_sample_contacts_endpoint_returns_clusters() -> None:
    client = TestClient(create_app())

    response = client.get("/api/samples/contacts?min_score=70")

    payload = response.json()
    assert response.status_code == 200
    assert payload["cluster_count"] == 2
    assert payload["merge_count"] == 2


def test_analyze_upload_accepts_csv_file() -> None:
    client = TestClient(create_app())
    csv_bytes = (
        b"Record ID,Email,First Name,Last Name\n"
        b"101,alice@example.com,Alice,Smith\n"
        b"102,alice@example.com,Alicia,Smith\n"
    )

    response = client.post(
        "/api/analyze",
        data={"object_type": "contacts", "min_score": "70"},
        files={"csv_file": ("contacts.csv", csv_bytes, "text/csv")},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["cluster_count"] == 1
    assert payload["clusters"][0]["actions"][0]["duplicate_id"] == "102"


def test_analyze_upload_rejects_header_only_csv() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/analyze",
        data={"object_type": "contacts", "min_score": "70"},
        files={"csv_file": ("contacts.csv", b"Record ID,Email,First Name,Last Name\n", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "CSV file does not contain any records."


def test_cli_can_dispatch_to_web_server(monkeypatch) -> None:
    called: dict[str, object] = {}

    def fake_run_server(host: str, port: int, reload: bool) -> None:
        called.update({"host": host, "port": port, "reload": reload})

    monkeypatch.setattr("hubspot_dedupe.cli.run_server", fake_run_server)

    main(["serve", "--host", "0.0.0.0", "--port", "9090", "--reload"])

    assert called == {"host": "0.0.0.0", "port": 9090, "reload": True}
