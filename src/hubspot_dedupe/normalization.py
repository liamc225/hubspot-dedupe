from __future__ import annotations

import re
from urllib.parse import urlparse


COMPANY_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "limited",
}


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip().lower()
    if not candidate:
        return None
    return re.sub(r"\s+", " ", candidate)


def normalize_email(value: str | None) -> str | None:
    return normalize_text(value)


def normalize_phone(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None

    digits = "".join(char for char in normalized if char.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits or None


def normalize_domain(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None

    stripped = normalized.removeprefix("https://").removeprefix("http://")
    stripped = stripped.removeprefix("www.")
    domain = stripped.split("/")[0]
    return domain or None


def domain_from_email(email: str | None) -> str | None:
    normalized = normalize_email(email)
    if normalized is None or "@" not in normalized:
        return None
    return normalized.split("@", 1)[1]


def domain_from_website(website: str | None) -> str | None:
    normalized = normalize_text(website)
    if normalized is None:
        return None

    value = normalized if "://" in normalized else f"https://{normalized}"
    parsed = urlparse(value)
    return normalize_domain(parsed.netloc)


def normalize_person_name(first_name: str | None, last_name: str | None) -> str | None:
    parts = [part for part in (normalize_text(first_name), normalize_text(last_name)) if part]
    if not parts:
        return None
    return " ".join(parts)


def normalize_company_name(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None

    tokens = re.findall(r"[a-z0-9]+", normalized)
    filtered = [token for token in tokens if token not in COMPANY_SUFFIXES]
    if not filtered:
        return normalized
    return " ".join(filtered)

