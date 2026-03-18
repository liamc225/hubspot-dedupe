# HubSpot Dedupe

`hubspot-dedupe` is an open source deduplication system for HubSpot contact and company exports. It reads HubSpot-style CSV files, scores likely duplicates, groups them into merge clusters, and recommends a master record with an audit trail explaining why.

## What It Does

- Detects duplicate contacts using email, phone, name similarity, company name, and domain overlap
- Detects duplicate companies using domain, website hostname, phone, and name similarity
- Produces deterministic merge clusters instead of only pairwise matches
- Picks a master record by completeness so merge reviews start from the best record
- Emits human-readable Markdown or machine-readable JSON output

## Why This Is Useful

HubSpot's native duplicate management is limited when records are missing exact identifiers. RevOps and GTM engineering teams often need a reviewable system that can explain why two records were matched before they automate merges.

## Quick Start

Run the contact example:

```bash
PYTHONPATH=src python3 -m hubspot_dedupe.cli contacts data/sample_contacts.csv
```

Run the company example:

```bash
PYTHONPATH=src python3 -m hubspot_dedupe.cli companies data/sample_companies.csv --format json
```

Run tests:

```bash
PYTHONPATH=src pytest
```

## Output Example

```text
Cluster C-001 | confidence: high | score: 100
Master: 101 (alice@example.com)
- Merge 102 into 101 | score: 100 | reasons: exact email match, exact phone match, same company domain
```

## Roadmap

- Add HubSpot private-app sync for reading records and writing merge actions
- Add exclusion rules for parent/child accounts and shared inboxes
- Add a review UI for human approval
- Add configurable rule packs by object type and business segment

