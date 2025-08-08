# Security and Compliance Guidelines

Scope
Global defaults derived from [RULES.md](RULES.md) and [PLAN.md](PLAN.md) for crawling, data handling, and artifact management.

Robots and Terms
- Respect robots.txt and site terms when crawling history or documents.
- Avoid aggressive parallelism; be a good citizen.

Networking hygiene
- Use explicit timeouts for all HTTP requests.
- Implement reasonable backoff and minimal retries to avoid hammering servers.
- Allow user-agent override when appropriate for transparency.

Caching and provenance
- Cache downloads to reduce repeated network access.
- Preserve provenance metadata: source URL, timestamp, and content type alongside artifacts.

Data handling
- Preserve source XHTML and metadata unmodified unless a flag authorizes transforms.
- Treat enrichment (e.g., PDF→MD via marker) as additive; do not replace originals.

Artifacts and binaries
- Do not commit large binaries to VCS; treat outputs as build artifacts.
- Prefer reproducible pipelines; document tool versions when relevant.

Access control and secrets
- Keep credentials out of the repo and CI logs.
- Use environment variables or local config files excluded from version control.

Compliance logging
- Emit clear [INFO]/[WARN] lines describing network failures, backoffs, and degraded behavior.
- Example logging format:
  - [INFO] Fetching history index
  - [WARN] marker conversion failed for file.pdf: error text