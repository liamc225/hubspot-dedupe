# HubSpot Dedupe

`hubspot-dedupe` is an open source deduplication engine for HubSpot contact and company exports. It reads HubSpot-style CSV files, scores likely duplicates, groups them into merge clusters, and recommends a master record with a clear audit trail explaining why the match happened.

The repo now includes a static frontend in [`docs/`](docs/) for a public-facing product page and interactive sample walkthrough. It is designed to be published via GitHub Pages alongside the Python package.

## Why It Exists

HubSpot's native duplicate management works best when records share exact identifiers. Real RevOps datasets are noisier: phone formats drift, company names vary, websites are incomplete, and duplicate review still needs an explanation a human can trust before merges happen.

This project focuses on three things:

- Deterministic matching logic for contact and company exports
- Cluster-based merge recommendations instead of isolated pair matches
- Explainable output that can be reviewed by ops teams before automation

## Features

- Contact matching using email, phone, name similarity, company, and domain overlap
- Company matching using domain, website hostname, phone, and normalized name
- Deterministic clustering with master-record selection based on completeness
- Markdown output for human review and JSON output for downstream systems
- Sample datasets and tests that document the expected behavior
- A GitHub Pages-ready frontend for positioning, demos, and distribution

## Quick Start

Install the package in editable mode:

```bash
python3 -m pip install -e .
```

Run the contact example:

```bash
hubspot-dedupe contacts data/sample_contacts.csv
```

Run the company example as JSON:

```bash
hubspot-dedupe companies data/sample_companies.csv --format json
```

You can also use the module entrypoint directly:

```bash
python3 -m hubspot_dedupe.cli contacts data/sample_contacts.csv
```

Run tests:

```bash
pytest
```

## Sample Output

```text
Cluster C-001 | confidence: high | score: 100
Master: 101 (alice@example.com)
- Merge 102 into 101 | score: 100 | reasons: exact email match, exact phone match, same company, same company domain
```

## Frontend

The static site lives in [`docs/`](docs/). It gives the project a public landing page with a modern visual treatment, product framing, and interactive sample clusters based on the included CSV fixtures.

Preview it locally:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`.

## Project Layout

- [`src/hubspot_dedupe`](src/hubspot_dedupe): matching engine, models, normalization, scoring, and CLI
- [`tests`](tests): engine and scoring tests
- [`data`](data): sample HubSpot-style CSV exports
- [`docs`](docs): GitHub Pages-ready frontend

## Roadmap

- Add HubSpot private-app sync for reading records and writing merge actions
- Add exclusion rules for parent/child accounts and shared inboxes
- Add a review UI for human approval workflows
- Add configurable rule packs by object type and business segment

## License

MIT. See [`LICENSE`](LICENSE).
