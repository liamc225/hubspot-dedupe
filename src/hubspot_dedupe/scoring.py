from __future__ import annotations

from difflib import SequenceMatcher

from hubspot_dedupe.models import CompanyRecord, ContactRecord, PairMatch
from hubspot_dedupe.normalization import (
    domain_from_email,
    domain_from_website,
    is_public_email_domain,
    normalize_company_name,
    normalize_domain,
    normalize_email,
    normalize_person_name,
    normalize_phone,
)


def _similarity(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def score_contact_pair(left: ContactRecord, right: ContactRecord) -> PairMatch:
    score = 0
    reasons: list[str] = []

    left_email = normalize_email(left.email)
    right_email = normalize_email(right.email)
    if left_email and left_email == right_email:
        score += 70
        reasons.append("exact email match")

    left_phone = normalize_phone(left.phone or left.mobile_phone)
    right_phone = normalize_phone(right.phone or right.mobile_phone)
    if left_phone and left_phone == right_phone:
        score += 35
        reasons.append("exact phone match")

    left_name = normalize_person_name(left.first_name, left.last_name)
    right_name = normalize_person_name(right.first_name, right.last_name)
    if left_name and left_name == right_name:
        score += 25
        reasons.append("exact full-name match")
    elif _similarity(left_name, right_name) >= 0.92:
        score += 15
        reasons.append("similar full name")

    left_company = normalize_company_name(left.company)
    right_company = normalize_company_name(right.company)
    if left_company and left_company == right_company:
        score += 15
        reasons.append("same company")
    elif _similarity(left_company, right_company) >= 0.9:
        score += 10
        reasons.append("similar company")

    left_domain = domain_from_email(left.email) or domain_from_website(left.website)
    right_domain = domain_from_email(right.email) or domain_from_website(right.website)
    if left_domain and left_domain == right_domain and not is_public_email_domain(left_domain):
        score += 15
        reasons.append("same company domain")

    return PairMatch(
        left_id=left.record_id,
        right_id=right.record_id,
        score=min(score, 100),
        reasons=reasons,
    )


def score_company_pair(left: CompanyRecord, right: CompanyRecord) -> PairMatch:
    score = 0
    reasons: list[str] = []

    left_domain = normalize_domain(left.domain) or domain_from_website(left.website)
    right_domain = normalize_domain(right.domain) or domain_from_website(right.website)
    if left_domain and left_domain == right_domain:
        score += 60
        reasons.append("exact domain match")

    left_phone = normalize_phone(left.phone)
    right_phone = normalize_phone(right.phone)
    if left_phone and left_phone == right_phone:
        score += 20
        reasons.append("exact phone match")

    left_name = normalize_company_name(left.name)
    right_name = normalize_company_name(right.name)
    if left_name and left_name == right_name:
        score += 30
        reasons.append("exact company-name match")
    elif _similarity(left_name, right_name) >= 0.9:
        score += 18
        reasons.append("similar company name")

    if left.city and right.city and left.city.strip().lower() == right.city.strip().lower():
        score += 5
        reasons.append("same city")

    return PairMatch(
        left_id=left.record_id,
        right_id=right.record_id,
        score=min(score, 100),
        reasons=reasons,
    )
