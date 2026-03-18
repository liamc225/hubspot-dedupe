from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from itertools import combinations

from hubspot_dedupe.models import CompanyRecord, ContactRecord, DuplicateCluster, ObjectType, PairMatch, Record
from hubspot_dedupe.normalization import (
    domain_from_email,
    domain_from_website,
    normalize_company_name,
    normalize_domain,
    normalize_email,
    normalize_person_name,
    normalize_phone,
)
from hubspot_dedupe.scoring import score_company_pair, score_contact_pair


class _UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parents = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parents[value]
        if parent != value:
            self.parents[value] = self.find(parent)
        return self.parents[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parents[right_root] = left_root


def find_duplicate_clusters(
    object_type: ObjectType,
    records: list[Record],
    min_score: int = 70,
) -> list[DuplicateCluster]:
    if object_type == "contacts":
        typed_records = [record for record in records if isinstance(record, ContactRecord)]
        pair_matches = _score_contact_candidates(typed_records, min_score)
    else:
        typed_records = [record for record in records if isinstance(record, CompanyRecord)]
        pair_matches = _score_company_candidates(typed_records, min_score)

    record_map = {record.record_id: record for record in typed_records}
    if not pair_matches:
        return []

    union_find = _UnionFind(list(record_map))
    for pair_match in pair_matches:
        union_find.union(pair_match.left_id, pair_match.right_id)

    groups: dict[str, list[Record]] = {}
    for record_id, record in record_map.items():
        root = union_find.find(record_id)
        groups.setdefault(root, []).append(record)

    clusters: list[DuplicateCluster] = []
    cluster_index = 1
    for group in groups.values():
        if len(group) < 2:
            continue

        group_ids = {record.record_id for record in group}
        group_matches = [
            pair_match
            for pair_match in pair_matches
            if pair_match.left_id in group_ids and pair_match.right_id in group_ids
        ]
        if not group_matches:
            continue

        master_record = _select_master_record(group)
        score = max(pair_match.score for pair_match in group_matches)
        confidence = _confidence_label(score)
        cluster_id = f"{object_type[0].upper()}-{cluster_index:03d}"
        clusters.append(
            DuplicateCluster(
                cluster_id=cluster_id,
                object_type=object_type,
                master_record=master_record,
                records=sorted(group, key=lambda record: record.record_id),
                pair_matches=sorted(group_matches, key=lambda match: match.score, reverse=True),
                confidence=confidence,
                score=score,
            )
        )
        cluster_index += 1

    return clusters


def cluster_to_dict(cluster: DuplicateCluster) -> dict[str, object]:
    return {
        "cluster_id": cluster.cluster_id,
        "object_type": cluster.object_type,
        "confidence": cluster.confidence,
        "score": cluster.score,
        "master_record": asdict(cluster.master_record),
        "records": [asdict(record) for record in cluster.records],
        "pair_matches": [asdict(pair_match) for pair_match in cluster.pair_matches],
    }


def _score_contact_candidates(records: list[ContactRecord], min_score: int) -> list[PairMatch]:
    candidate_pairs = _candidate_pairs(records, _contact_block_keys)
    return [
        pair_match
        for left, right in candidate_pairs
        for pair_match in [score_contact_pair(left, right)]
        if pair_match.score >= min_score
    ]


def _score_company_candidates(records: list[CompanyRecord], min_score: int) -> list[PairMatch]:
    candidate_pairs = _candidate_pairs(records, _company_block_keys)
    return [
        pair_match
        for left, right in candidate_pairs
        for pair_match in [score_company_pair(left, right)]
        if pair_match.score >= min_score
    ]


def _candidate_pairs(
    records: list[Record],
    block_key_builder: Callable[[Record], list[str]],
) -> list[tuple[Record, Record]]:
    buckets: dict[str, list[Record]] = {}
    for record in records:
        for key in block_key_builder(record):
            buckets.setdefault(key, []).append(record)

    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[Record, Record]] = []
    for bucket_records in buckets.values():
        for left, right in combinations(bucket_records, 2):
            pair_key = tuple(sorted((left.record_id, right.record_id)))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            pairs.append((left, right))

    return pairs


def _contact_block_keys(record: ContactRecord) -> list[str]:
    keys: list[str] = []
    email = normalize_email(record.email)
    phone = normalize_phone(record.phone or record.mobile_phone)
    name = normalize_person_name(record.first_name, record.last_name)
    company = normalize_company_name(record.company)
    domain = domain_from_email(record.email) or domain_from_website(record.website)

    if email:
        keys.append(f"email:{email}")
    if phone:
        keys.append(f"phone:{phone}")
    if name and domain:
        keys.append(f"name-domain:{name}:{domain}")
    if name and company:
        keys.append(f"name-company:{name}:{company}")
    return keys


def _company_block_keys(record: CompanyRecord) -> list[str]:
    keys: list[str] = []
    domain = normalize_domain(record.domain) or domain_from_website(record.website)
    name = normalize_company_name(record.name)
    phone = normalize_phone(record.phone)

    if domain:
        keys.append(f"domain:{domain}")
    if phone:
        keys.append(f"phone:{phone}")
    if name:
        keys.append(f"name:{name}")
    return keys


def _select_master_record(records: list[Record]) -> Record:
    return sorted(
        records,
        key=lambda record: (-_record_completeness(record), _sortable_record_id(record.record_id)),
    )[0]


def _record_completeness(record: Record) -> int:
    if isinstance(record, ContactRecord):
        weights = [
            (record.email, 4),
            (record.phone or record.mobile_phone, 3),
            (record.first_name, 1),
            (record.last_name, 1),
            (record.company, 1),
            (record.website, 1),
            (record.lifecycle_stage, 1),
            (record.owner, 1),
        ]
    else:
        weights = [
            (record.domain, 4),
            (record.website, 2),
            (record.phone, 3),
            (record.name, 2),
            (record.city, 1),
            (record.state, 1),
            (record.country, 1),
            (record.owner, 1),
        ]

    return sum(weight for value, weight in weights if isinstance(value, str) and value.strip())


def _sortable_record_id(record_id: str) -> tuple[int, str]:
    if record_id.isdigit():
        return int(record_id), record_id
    return 10**12, record_id


def _confidence_label(score: int) -> str:
    if score >= 90:
        return "high"
    if score >= 75:
        return "medium"
    return "review"
