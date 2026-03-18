from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from hubspot_dedupe.models import CompanyRecord, ContactRecord, ObjectType, Record


CONTACT_ALIASES = {
    "record_id": ["Record ID", "Record Id", "hs_object_id", "Contact ID"],
    "email": ["Email", "E-mail"],
    "first_name": ["First Name", "firstname"],
    "last_name": ["Last Name", "lastname"],
    "phone": ["Phone Number", "Phone"],
    "mobile_phone": ["Mobile Phone Number", "Mobile Phone"],
    "company": ["Company Name", "Company"],
    "website": ["Website URL", "Website"],
    "lifecycle_stage": ["Lifecycle Stage", "lifecyclestage"],
    "owner": ["Contact owner", "HubSpot Owner", "Owner"],
}


COMPANY_ALIASES = {
    "record_id": ["Record ID", "Record Id", "hs_object_id", "Company ID"],
    "name": ["Company name", "Name", "Company Name"],
    "domain": ["Company domain name", "Domain", "Domain Name"],
    "website": ["Website URL", "Website"],
    "phone": ["Phone Number", "Phone"],
    "city": ["City"],
    "state": ["State/Region", "State"],
    "country": ["Country/Region", "Country"],
    "owner": ["Company owner", "HubSpot Owner", "Owner"],
}


def _pick_value(row: dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in row and row[alias].strip():
            return row[alias].strip()
    return None


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _read_rows_from_text(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(csv_text))
    return [dict(row) for row in reader]


def load_records(path: str, object_type: ObjectType) -> list[Record]:
    rows = _read_rows(Path(path))
    return _load_records_from_rows(rows, object_type)


def load_records_from_text(csv_text: str, object_type: ObjectType) -> list[Record]:
    rows = _read_rows_from_text(csv_text)
    return _load_records_from_rows(rows, object_type)


def load_records_from_bytes(csv_bytes: bytes, object_type: ObjectType) -> list[Record]:
    try:
        csv_text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV file must be UTF-8 encoded.") from exc

    return load_records_from_text(csv_text, object_type)


def _load_records_from_rows(rows: list[dict[str, str]], object_type: ObjectType) -> list[Record]:
    if object_type == "contacts":
        return [_build_contact(row) for row in rows]
    return [_build_company(row) for row in rows]


def _build_contact(row: dict[str, str]) -> ContactRecord:
    record_id = _pick_value(row, CONTACT_ALIASES["record_id"])
    if not record_id:
        raise ValueError("Contact row is missing a HubSpot record id")

    return ContactRecord(
        record_id=record_id,
        email=_pick_value(row, CONTACT_ALIASES["email"]),
        first_name=_pick_value(row, CONTACT_ALIASES["first_name"]),
        last_name=_pick_value(row, CONTACT_ALIASES["last_name"]),
        phone=_pick_value(row, CONTACT_ALIASES["phone"]),
        mobile_phone=_pick_value(row, CONTACT_ALIASES["mobile_phone"]),
        company=_pick_value(row, CONTACT_ALIASES["company"]),
        website=_pick_value(row, CONTACT_ALIASES["website"]),
        lifecycle_stage=_pick_value(row, CONTACT_ALIASES["lifecycle_stage"]),
        owner=_pick_value(row, CONTACT_ALIASES["owner"]),
        raw=row,
    )


def _build_company(row: dict[str, str]) -> CompanyRecord:
    record_id = _pick_value(row, COMPANY_ALIASES["record_id"])
    name = _pick_value(row, COMPANY_ALIASES["name"])
    if not record_id or not name:
        raise ValueError("Company row is missing a record id or name")

    return CompanyRecord(
        record_id=record_id,
        name=name,
        domain=_pick_value(row, COMPANY_ALIASES["domain"]),
        website=_pick_value(row, COMPANY_ALIASES["website"]),
        phone=_pick_value(row, COMPANY_ALIASES["phone"]),
        city=_pick_value(row, COMPANY_ALIASES["city"]),
        state=_pick_value(row, COMPANY_ALIASES["state"]),
        country=_pick_value(row, COMPANY_ALIASES["country"]),
        owner=_pick_value(row, COMPANY_ALIASES["owner"]),
        raw=row,
    )
