# HubSpot Dedupe

`hubspot-dedupe` is an open source deduplication engine for HubSpot contact and company exports. It reads HubSpot-style CSV files, scores likely duplicates, groups them into merge clusters, and recommends a master record with a clear audit trail explaining why the match happened.

This repo ships with a self-hosted web UI so ops teams can upload exports, review duplicate clusters, and validate merge recommendations in the browser without sending data to a third-party service.

## Why It Exists

HubSpot's native duplicate management works best when records share exact identifiers. Real RevOps datasets are noisier: phone formats drift, company names vary, websites are incomplete, and duplicate review still needs an explanation a human can trust before merges happen.

This project focuses on four things:

- Deterministic matching logic for contact and company exports
- Cluster-based merge recommendations instead of isolated pair matches
- Explainable output that can be reviewed by ops teams before automation
- A self-hosted browser UI for upload, scoring, and review

## Features

- Contact matching using email, phone, name similarity, company, and domain overlap
- Company matching using domain, website hostname, phone, and normalized name
- Deterministic clustering with master-record selection based on completeness
- Markdown output for human review and JSON output for downstream systems
- Self-hosted web UI with CSV upload, sample datasets, and cluster review
- Safer CSV validation with clear errors for empty or malformed uploads
- Public-email suppression so shared consumer domains do not create noisy name-domain matches

## Quick Start

Install the package:

```bash
python3 -m pip install -e .
```

Start the web UI:

```bash
hubspot-dedupe serve --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

Run the contact example from the CLI:

```bash
hubspot-dedupe contacts data/sample_contacts.csv
```

Run the company example as JSON:

```bash
hubspot-dedupe companies data/sample_companies.csv --format json
```

Run tests:

```bash
python3 -m pip install -e ".[dev]"
pytest
```

## Sample Output

```text
Cluster C-001 | confidence: high | score: 100
Master: 101 (alice@example.com)
- Merge 102 into 101 | score: 100 | reasons: exact email match, exact phone match, same company, same company domain
```

## Self-Hosted UI

The web app is built into the Python package and runs locally with the same matching engine as the CLI. It supports:

- Uploading contact or company CSV exports directly in the browser
- Adjusting the minimum duplicate score before analysis
- Loading bundled sample datasets for quick verification
- Reviewing cluster confidence, recommended merge actions, and match reasons

## Project Layout

- [`src/hubspot_dedupe`](src/hubspot_dedupe): matching engine, models, normalization, scoring, and CLI
- [`src/hubspot_dedupe/web`](src/hubspot_dedupe/web): self-hosted web UI and API
- [`tests`](tests): engine and web tests
- [`data`](data): sample HubSpot-style CSV exports

## What It Is Not

- Not a direct HubSpot merge client yet
- Not a hosted SaaS product
- Not an ML classifier with opaque scoring

## Roadmap

- Add HubSpot private-app sync for reading records and writing merge actions
- Add exclusion rules for parent/child accounts and shared inboxes
- Add persistent review workflows and saved analysis history
- Add configurable rule packs by object type and business segment

## License

MIT. See [`LICENSE`](LICENSE).
