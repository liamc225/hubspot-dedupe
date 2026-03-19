import json

from hubspot_dedupe.cli import render_markdown
from hubspot_dedupe.engine import cluster_to_dict, find_duplicate_clusters
import pytest

from hubspot_dedupe.io import load_records, load_records_from_text
from hubspot_dedupe.models import CompanyRecord, ContactRecord


def test_contact_duplicates_cluster_by_email_and_phone() -> None:
    records = [
        ContactRecord(
            record_id="101",
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
            phone="(312) 555-0101",
            company="Example Inc",
        ),
        ContactRecord(
            record_id="102",
            email="alice@example.com",
            first_name="Alicia",
            last_name="Smith",
            phone="3125550101",
            company="Example",
            website="https://example.com",
        ),
        ContactRecord(
            record_id="103",
            email="bob@example.com",
            first_name="Bob",
            last_name="Stone",
        ),
    ]

    clusters = find_duplicate_clusters("contacts", records)

    assert len(clusters) == 1
    assert clusters[0].master_record.record_id == "102"
    assert clusters[0].pair_matches[0].score == 100


def test_company_duplicates_cluster_by_domain_and_name() -> None:
    records = [
        CompanyRecord(record_id="201", name="Acme, Inc.", domain="acme.com", phone="312-555-0109", city="Chicago"),
        CompanyRecord(record_id="202", name="Acme Incorporated", website="https://acme.com", phone="3125550109", city="Chicago"),
        CompanyRecord(record_id="203", name="Northwind", domain="northwind.io"),
    ]

    clusters = find_duplicate_clusters("companies", records, min_score=70)

    assert len(clusters) == 1
    assert clusters[0].master_record.record_id == "201"
    assert clusters[0].confidence == "high"


def test_loader_maps_hubspot_headers_from_sample_files() -> None:
    contacts = load_records("data/sample_contacts.csv", "contacts")
    companies = load_records("data/sample_companies.csv", "companies")

    assert contacts[0].record_id == "101"
    assert contacts[1].email == "alice@example.com"
    assert companies[0].name == "Acme, Inc."
    assert companies[1].domain is None


def test_markdown_output_contains_merge_recommendation() -> None:
    records = [
        ContactRecord(record_id="101", email="alice@example.com", first_name="Alice", last_name="Smith"),
        ContactRecord(record_id="102", email="alice@example.com", first_name="Alice", last_name="Smith"),
    ]

    cluster = find_duplicate_clusters("contacts", records)[0]
    output = render_markdown("contacts", [cluster])

    assert "Merge 102 into 101" in output or "Merge 101 into 102" in output


def test_cluster_to_dict_is_json_serializable() -> None:
    records = [
        ContactRecord(record_id="101", email="alice@example.com"),
        ContactRecord(record_id="102", email="alice@example.com"),
    ]

    cluster = find_duplicate_clusters("contacts", records)[0]
    payload = cluster_to_dict(cluster)

    assert json.loads(json.dumps(payload))["cluster_id"] == cluster.cluster_id


def test_public_email_domains_do_not_create_name_domain_matches() -> None:
    records = [
        ContactRecord(record_id="101", email="alex@gmail.com", first_name="Alex", last_name="Morgan"),
        ContactRecord(record_id="102", email="alex@gmail.com".replace("alex", "alex.work"), first_name="Alex", last_name="Morgan"),
    ]

    assert find_duplicate_clusters("contacts", records, min_score=1) == []


def test_loader_rejects_header_only_csv() -> None:
    with pytest.raises(ValueError, match="does not contain any records"):
        load_records_from_text("Record ID,Email,First Name,Last Name\n", "contacts")


def test_loader_rejects_non_hubspot_headers() -> None:
    with pytest.raises(ValueError, match="do not look like a HubSpot contacts export"):
        load_records_from_text("id,mail,given_name\n1,test@example.com,Alice\n", "contacts")
