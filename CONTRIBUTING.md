# Contributing to Brisa

Contributions to routing, data quality, accessibility, reproducibility, and documentation are welcome. Review the [README](README.md), [architecture](docs/architecture.md), [known issues](docs/known-issues.md), and [code of conduct](CODE_OF_CONDUCT.md) first.

## Workflow

1. For a substantial feature or model change, open an issue with the problem, evidence, and proposed scope. Small documentation corrections can go directly to a pull request.
2. Branch from `main` and keep changes focused. Avoid mixing unrelated refactors with behavior changes.
3. Keep GIS/scoring in backend services; keep provider normalization outside visual components.
4. Update contracts and affected docs when public behavior changes.
5. Run the relevant checks and report their actual outcome, including known failures.

```bash
npm install
npm run lint
npm run build
cd backend
python -m pip install -r requirements.txt pytest pytest-asyncio
PRECOMPUTE_CACHE_ON_STARTUP=false python -m pytest -q
```

See [local setup](README.md#running-locally) for environment and GIS requirements. The existing suite has recorded failures; compare against [verification](docs/verification.md), and separate new regressions from upstream issues. Provider-backed changes need a representative manual check in addition to fixture tests.

## Good pull requests

Explain the concrete problem, resulting behavior, relevant trade-offs, and verification. For UI changes, include real screenshots. For scoring changes, explain units, normalization, affected datasets, cache rebuild requirements, and limitations. Do not call heuristic scores validated without independent evidence.

Do not commit API keys, local `.env` files, downloaded city-wide caches, or unrelated generated artifacts. Maintain data and tile attribution. Document required configuration without including real credentials.

## Reporting bugs

Include expected/actual behavior, reproducible steps, OS/browser/Python/Node versions, and relevant redacted logs. For routing/data issues, include profile, public test endpoints, cache versions, and source record counts when possible. Avoid publishing private trip/location history. Report security concerns through [SECURITY.md](SECURITY.md).
