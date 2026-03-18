from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Union


ObjectType = Literal["contacts", "companies"]


@dataclass(frozen=True)
class ContactRecord:
    record_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    company: str | None = None
    website: str | None = None
    lifecycle_stage: str | None = None
    owner: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CompanyRecord:
    record_id: str
    name: str
    domain: str | None = None
    website: str | None = None
    phone: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    owner: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


Record = Union[ContactRecord, CompanyRecord]


@dataclass(frozen=True)
class PairMatch:
    left_id: str
    right_id: str
    score: int
    reasons: list[str]


@dataclass(frozen=True)
class DuplicateCluster:
    cluster_id: str
    object_type: ObjectType
    master_record: Record
    records: list[Record]
    pair_matches: list[PairMatch]
    confidence: str
    score: int
